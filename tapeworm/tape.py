#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Determines blobs that should be concatenated
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import sys
import itertools
import math

import numpy as np

import multiworm
enumerate = multiworm.util.enumerate
from multiworm.readers.blob import parse as parse_blob
from . import scoring

FRAME_RATE = 14

# Absolute requirements for candidates.  Extremely liberal criteria.
MAX_FRAME_GAP = 500 #: Maximum gap time in frames to consider (1 s ~= 10 frames)
MAX_WORM_SPEED = 1.37 #: Worms move at some finite speed, measured in px/frame.
MAX_OBS_FRAC = 0.90 #: Assume that the observed worms were only moving this fraction of theoretical maximum
WORM_ERROR = 10 #: Offset in pixels to add on max speed bounding "cone".

def euclid(a, b):
    """
    Returns the Euclidean distance between `a` and `b`.
    """
    return np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float))

def absolute_displacement(centroid, reverse=False):
    """
    Given a sequence of X-Y coordinates, return the absolute distance from 
    each point to the first point.

    Parameters
    ----------
    centroid : array_like
        A sequence of X-Y coordinate pairs.

    Keyword Arguments
    -----------------
    reverse : bool
        Reverse the centroid sequence before taking the absolute values
    """
    if reverse:
        centroid = centroid[::-1]
    centroid = np.array(centroid)
    centroid -= centroid[0]

    # http://stackoverflow.com/a/12712725/194586
    displacement = np.sqrt(np.einsum('...i,...i', centroid, centroid, dtype='float64'))
    return displacement

def jagged_mask(data):
    """
    Stacks up variable length series into a faux-jagged (masked) array.
    """
    h_size = max(len(trace) for trace in data)
    # stack up data, mask off non-existant values (np can't do jagged arrays)
    dstack = np.ma.masked_all((len(data), h_size))
    for i, trace in enumerate(data):
        len_trace = len(trace)
        dstack[i, 0:len_trace] = trace

    return dstack

def find_candidates(ends, starts, **params):
    """
    Finds any possible connection between *ends* and *starts* within a 
    'cone' projected forward through time and area.

    Parameters
    ----------
    ends, starts : numpy.ndarray
        Numpy structured array containing blob end- and start-points--where 
        tracking was lost and found--with the following column names:

        * `bid` - Blob ID
        * `loc` - X-Y coordinates of where blob was lost
        * `f` - Frame blob lost/found

    Keyword Arguments
    -----------------
    max_fgap : number
        Maximum gap length to accept in frames.  The 'height' of the cone 
        to search in.

    max_speed : number
        Maximum speed to include connections in pixels per frame.  The 
        'slope' of the cone.

    error : number
        Acommodate jitter in the track locations by accepting deviations of 
        up to this number of pixels at all times.

    Returns
    -------
    candidates : dict
        A dictionary with all end blob IDs as keys, and a dictionary of
        possible starts as values.  In the latter dictionary, keys are IDs
        and the value is a third dictionary with the fields `d` containing 
        the distance gap, and `f` with the frame gap.
    """
    p = {
        'max_fgap': MAX_FRAME_GAP,
        'max_speed': MAX_WORM_SPEED / MAX_OBS_FRAC,
        'error': WORM_ERROR,
    }
    if params:
        p.update(params)

    candidates = {}
    for blob_a in ends:
        a_bid = int(blob_a['bid'])
        candidates[a_bid] = {}
        for blob_b in starts[np.logical_and(
                    blob_a['f'] < starts['f'], 
                    starts['f'] <= blob_a['f'] + p['max_fgap']
                )]:
            b_bid = int(blob_b['bid'])
            f_gap = blob_b['f'] - blob_a['f']
            d_gap = euclid(blob_a['loc'], blob_b['loc'])

            # check if it's in the 'cone'
            if (d_gap <= p['error'] + f_gap * p['max_speed']):
                # a->b is possible, save it.
                candidates[a_bid][b_bid] = {
                            'd': d_gap, 
                            'f': f_gap,
                        }

    return candidates

def join_segments(diedges, nodes=None):
    """
    Join together directed edges into subgraphs.

    Parameters
    ----------
    diedges : iterable
        An iterable of directed edges to connect.  Maximum of one child and 
        one parent per node.

    Keyword Arguments
    -----------------
    nodes : set
        If a set of nodes is provided, the return value will include the set 
        of nodes that weren't included in any of the *traces*.

    Returns
    -------
    traces : list
        Directed subgraphs
    free_nodes : set
        Only returned if *nodes* is provided.
    """
    traces = []

    # value checks
    starts = set(edge[0] for edge in diedges)
    ends = set(edge[1] for edge in diedges)
    if len(starts) != len(diedges):
        raise ValueError("Node has more than one child.")
    if len(ends) != len(diedges):
        raise ValueError("Node has more than one parent.")

    if nodes:
        for edge in diedges:
            for node in edge:
                if node not in nodes:
                    raise ValueError("Edge contains node not in 'nodes'")

    # stitch all edges together
    for edge in diedges:
        for trace in traces:
            if trace[0] == edge[-1]:
                trace.insert(0, edge[0])
                break
            elif trace[-1] == edge[0]:
                trace.append(edge[-1])
                break
        else:
            traces.append(list(edge))

    # remove joined segment nodes from the set to produce 'free' nodes.
    if nodes:
        for trace in traces:
            for node in trace:
                nodes.remove(node)
        return traces, nodes

    return traces


class MultiblobExperiment(multiworm.Experiment):
    """
    A version of the MWT experiment reader 
    (:class:`multiworm.experiment.Experiment`) that accepts an 
    iterable of blob IDs to parse and patches them together into contiguous 
    blobs.

    The caller is responsible for attaching the relevant multiblob metadata 
    to the output from :func:`parse_blob`.
    """
    def _void_line(self, frame):
        """
        Returns a "null line" with the provided *frame* and corresponding
        time.
        """
        time = self.frame_times[frame]
        # the variable number of spaces between fields are in the actual 
        # files but aren't documented why one or the other, and it never 
        # se5
        return '{frame} {time}  -1 -1  -1  0 0  0  -1 -1'.format(
            frame=frame, time=time)

    def _blob_lines(self, bids):
        """
        Accepts sequences of blob IDs in addition to single IDs, then 
        yields them 
        """
        last_line = None
        try:
            bids = iter(bids)
        except TypeError:
            bids = [bids]

        for bid in bids:
            lines = super(MultiblobExperiment, self)._blob_lines(bid)
            first_line = six.next(lines)

            # fill in gaps
            if last_line is not None:
                # determine gap between loss/finding of consecutive blobs
                end_frame = parse_blob([last_line])['frame'][0]
                start_frame = parse_blob([first_line])['frame'][0]
                if start_frame <= end_frame:
                    raise ValueError("Specified blobs overlap or are not consecutive.")
                # and fill
                for missing_frame in range(end_frame + 1, start_frame):
                    yield self._void_line(missing_frame)

            for line in itertools.chain([first_line], lines):
                yield line

            last_line = line


class Taper(object):
    """
    Attach disconnected blob tracks to one another.

    After initialization, add additional filters if desired to the ``plate``
    :class:`multiworm.experiment.Experiment` member object, then
    :func:`load_data`.  

    Parameters
    ----------
    directory : str
        Directory of the MWT data set to process.

    Keyword Arguments
    -----------------
    min_move : float
        Minimum amount individual blobs needs to traverse (bounding box 
        linear size) relative to their average body length prior to 
        concatenating.  Default: **2**

    min_time : float
        Minimum time in seconds individual blob traces need to exist.
        Default: **10**

    horizon : float
        How far out in seconds to consider blob joins. 
        Default: **50**
    """
    def __init__(self, directory, min_move=2, min_time=10, horizon=50):
        self.plate = MultiblobExperiment(directory)
        self.plate.add_summary_filter(multiworm.filters.summary_lifetime_minimum(min_time))
        self.plate.add_filter(multiworm.filters.relative_move_minimum(min_move))

        self.horizon_frames = horizon * FRAME_RATE

        self.starts = None # (bid, x, y, f)
        self.ends = None # (bid, x, y, f)
        self.displacements = None

    def _condense_blob(self, blob):
        """
        The only statistics we care about:

            1. When (in frames) blob was lost and found
            2. Where (x, y) blob was lost and found
            3. The centroid relative displacement for *horizon* seconds
        """
        simple_blob = {
                'born_f': blob['frame'][0],
                'died_f': blob['frame'][-1],
                'born_at': blob['centroid'][0],
                'died_at': blob['centroid'][-1],
                'centroid': blob['centroid'][:self.horizon_frames],
            }

        return simple_blob

    def _allocate_zeros(self, width=1, dtype=None):
        if dtype:
            dtype = multiworm.util.dtype(dtype)
        return np.zeros((self.plate.max_blobs, width), dtype=dtype)

    def load_data(self, show_progress=False):
        """
        Parse, filter, and determine a scoring method for blobs.  Optionally
        `show_progress` of the process, as this is the longest method call.
        """
        self.plate.load_summary()
        terminal_fields = [('bid', 'int32'), ('loc', '2int16'), ('f', 'int32')]
        self.starts = self._allocate_zeros(dtype=terminal_fields)
        self.ends = self._allocate_zeros(dtype=terminal_fields)
        displacements = []

        for i, blob in enumerate(self.plate.good_blobs()):
            bid, bdata = blob
            bdata = self._condense_blob(bdata)
            blob = None

            self.starts[i] = bid, bdata['born_at'], bdata['born_f']
            self.ends[i] = bid, bdata['died_at'], bdata['died_f']
            displacements.append(absolute_displacement(bdata['centroid']))

            if show_progress:
                done, total = self.plate.progress()
                percent = 100*done/total
                print(' Loading... [ {:-<50s} ] {}/{} ({:.1f}%)      '.format(
                        '#'*int(percent//2), done, total, percent), 
                        end='\r')
                sys.stdout.flush()

        if show_progress:
            print() # just a newline to move on from the bar graph.

        # crop arrays
        self.starts.resize(i + 1)
        self.ends.resize(i + 1)

        displacements = jagged_mask(displacements)
        self.scorer = scoring.DisplacementScorer(displacements)

    def find_candidates(self, max_fgap=500):
        """
        Finds all candidate joins within the given number of frames and 
        distance.
        """
        self.candidates = find_candidates(self.ends, self.starts, max_fgap=max_fgap)

    def score_candidates(self):
        for lost_bid, connections in six.iteritems(self.candidates):
            for found_bid, connection in six.iteritems(connections):
                connection['score'] = math.log10(self.scorer(connection['f'], connection['d']).max())
                print('{0:5d} --> {1:<5d} : f={2:3d}, d={3:5.1f}, log_score={4:.2f}'.format(
                        lost_bid, found_bid, connection['f'], connection['d'], connection['score']
                    ))

    def judge_candidates(self, log_threshold=-2):
        """
        Using the scores, determine how to patch worm segments together.
        """
        blob_ids = set(self.candidates)
        trace_edges = {}
        for lost_bid, connections in six.iteritems(self.candidates):
            hi_scorer = 0
            hi_score = -np.inf
            for found_bid, connection in six.iteritems(connections):
                if connection['score'] > hi_score:
                    hi_score_bid = found_bid
                    hi_score = connection['score']

            if hi_score >= log_threshold:
                # dictionary does a reverse-lookup of the connection and 
                # checks if a prior connection to a child was any better.
                try:
                    if trace_edges[hi_score_bid][1] < hi_score:
                        trace_edges[hi_score_bid] = (lost_bid, hi_score)
                except KeyError:
                    trace_edges[hi_score_bid] = (lost_bid, hi_score)

        # convert the awkward dictionary to a simple list of edges
        trace_edges = [(v[0], k) for k, v in six.iteritems(trace_edges)]

        self.patched_segments, self.unpatched_segments = join_segments(trace_edges, blob_ids)

        for trace in self.patched_segments:
            print(' -> '.join(str(bid) for bid in trace))

    def yield_candidates(self):
        """
        Generator that yields all patched segments
        """
        for bid in self.unpatched_segments:
            yield self.plate.parse_blob(bid)

        for trace in self.patched_segments:
            patched = self.plate.parse_blob(trace)
            patched['segments'] = trace
            yield patched
            patched = None # save mem

    def ThePeterProcedure(self):
        """
        Do all the things.  e.g. 

        ::

            for blob in tapeworm.Taper(mypath).ThePeterProcedure():
                ... # do something with 'blob'
        """
        self.load_data()
        self.find_candidates()
        self.score_candidates()
        self.judge_candidates()

        cans = self.yield_candidates()
        while True:
            yield six.next(cans)

if __name__ == '__main__':
    edges = [(1,2),(2,3),(4,5),(6,7),(8,6)]
    nodes = set(range(10))

    print(join_segments(edges, nodes))
