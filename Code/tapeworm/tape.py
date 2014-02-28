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
from . import scoring

FRAME_RATE = 14

# Absolute requirements for candidates.  Extremely liberal criteria.
MAX_FRAME_GAP = 500 #: Maximum gap time in frames to consider (1 s ~= 10 frames)
MAX_WORM_SPEED = 1.37 #: Worms move at some finite speed, measured in px/frame.
MAX_OBS_FRAC = 0.90 #: Assume that the observed worms were only moving this fraction of theoretical maximum
WORM_ERROR = 10 #: Offset in pixels to add on max speed bounding "cone".

def dist(a, b):
    """
    Reurns the Euclidean distance between *a* and *b*.
    """
    return np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float))

def abs_centroid(centroid, reverse=False):
    """
    OLD DOCS
    # Looks through *collection* for ``c_isgood`` ``seq_centroid`` blob paths.
    # Returns a list of NumPy arrays containing the absolute displacement at
    # each time point (frame) from the start.
    """
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
    ends : numpy.ndarray
        Numpy structured array containing blob endpoints--where tracking was 
        lost--with the following column names:
            * `bid` - Blob ID
            * `loc` - (X, Y) coordinates of where blob was lost
            * `f` - Frame blob lost

    starts : numpy.ndarray
        As *ends*, but where blob tracking began.

    Keyword Parameters
    ------------------
    max_fgap : number
        Maximum gap length to accept in frames.  The 'height' of the cone 
        to search in.
    max_speed : number
        Maximum speed to include connections in pixels per frame.  The 
        'slope' of the cone.
    error : number
        Acommodate jitter in the track locations by accepting deviations of 
        up to this number of pixels at all times.
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
            d_gap = dist(blob_a['loc'], blob_b['loc'])

            # check if it's in the 'cone'
            if (d_gap <= p['error'] + f_gap * p['max_speed']):
                # a->b is possible, save it.
                candidates[a_bid][b_bid] = {
                            'd': d_gap, 
                            'f': f_gap,
                        }

    return candidates


class Taper(object):
    def __init__(self, path, min_move=2, min_time=10, horizon=50):
        self.plate = multiworm.Experiment(path)
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
        Call to load data from the experiment and set up scoring method
        """
        self.plate.load_summary()
        terminal_fields = [('bid', 'int32'), ('loc', '2int16'), ('f', 'int32')]
        self.starts = self._allocate_zeros(dtype=terminal_fields)
        self.ends = self._allocate_zeros(dtype=terminal_fields)
        displacements = []

        #for i, blob in enumerate(itertools.islice(self.plate.good_blobs(), 100)):
        for i, blob in enumerate(self.plate.good_blobs()):
            bid, bdata = blob
            bdata = self._condense_blob(bdata)
            blob = None

            self.starts[i] = bid, bdata['born_at'], bdata['born_f']
            self.ends[i] = bid, bdata['died_at'], bdata['died_f']
            displacements.append(abs_centroid(bdata['centroid']))

            if show_progress:
                done, total = self.plate.progress()
                percent = 100*done/total
                print(' Loading... [ {:-<50s} ] {}/{} ({:.1f}%)      '.format(
                        '#'*int(percent//2), done, total, percent), 
                        end='\r')
                sys.stdout.flush()

        if show_progress:
            print()

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
                connection['score'] = self.scorer(connection['f'], connection['d'])
                print('{0:5d} --> {1:<5d} : f={2:3d}, d={3:5.1f}, log_score={4:.1f}'.format(
                        lost_bid, found_bid, connection['f'], connection['d'], math.log10(connection['score'].max())
                    ))
