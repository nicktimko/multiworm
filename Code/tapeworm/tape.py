#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Determines blobs that should be concatenated
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)
#from future.builtins import super

import sys
import itertools

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
    '''
    Reurns the Euclidean distance between *a* and *b*.
    '''
    return np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float))

def abs_centroid(centroid, reverse=False):
    '''
    OLD DOCS
    # Looks through *collection* for ``c_isgood`` ``seq_centroid`` blob paths.
    # Returns a list of NumPy arrays containing the absolute displacement at
    # each time point (frame) from the start.
    '''
    centroid = np.array(centroid)
    centroid -= centroid[0]

    # http://stackoverflow.com/a/12712725/194586
    displacement = np.sqrt(np.einsum('...i,...i', centroid, centroid, dtype='float64'))
    return displacement

def find_candidates(ends, starts, params=None):
    p = {
        'max_fgap': MAX_FRAME_GAP,
        'max_speed': MAX_WORM_SPEED / MAX_OBS_FRAC,
        'error': WORM_ERROR,
    }
    if params is not None:
        p.update(params)

    candidates = {}
    for blob_a in ends:
        candidates[blob_a['bid']] = {}
        for blob_b in starts[np.logical_and(
                    blob_a['f'] < starts['f'], 
                    starts['f'] <= blob_a['f'] + p['max_fgap']
                )]:
            f_gap = blob_b['f'] - blob_a['f']
            d_gap = dist(blob_a['loc'], blob_b['loc'])

            # check if it's in the 'cone'
            if (d_gap <= p['error'] + f_gap * p['max_speed']):
                # a->b is possible, save it.
                candidates[blob_a['bid']][blob_b['bid']] = {
                            'd': d_gap, 
                            'f': f_gap,
                        }

    return candidates


class Taper(object):
    def __init__(self, path, min_move=2, min_time=120, horizon=50):
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
        self.displacements = self._allocate_zeros(self.horizon_frames)

        for i, blob in enumerate(itertools.islice(self.plate.good_blobs(), 7)):
            bid, bdata = blob
            bdata = self._condense_blob(bdata)
            blob = None

            self.starts[i] = bid, bdata['born_at'], bdata['born_f']
            self.ends[i] = bid, bdata['died_at'], bdata['died_f']
            self.displacements[i] = abs_centroid(bdata['centroid'])

            if show_progress:
                done, total = self.plate.progress()
                percent = 100*done/total
                print(' Loading... [ {:-<50s} ] {}/{} ({:.1f}%)    '.format(
                        '#'*int(percent//2), done, total, percent), 
                        end='\r')
                sys.stdout.flush()

        if show_progress:
            print()

        # crop arrays
        self.starts.resize(i + 1, 4)
        self.ends.resize(i + 1, 4)
        self.displacements.resize(i + 1, self.horizon_frames)

        self.scorer = scoring.DisplacementScorer(self.displacements)

    # def find_candidates(self, max_fgap=500, max_dgap=400):
    #     """
    #     Finds all candidate joins within the given number of frames and 
    #     distance.
    #     """
    #     #for blob in self.ends:

    #     MAX_DIST = WORM_ERROR + MAX_FRAME_GAP * MAX_WORM_SPEED / MAX_OBS_FRAC

    #     candidates = {}
    #     for blob_a in self.ends:
    #         candidates[blob_a['bid']] = []
    #         for blob_b in collection.find({
    #                 'c_isgood': True,
    #                 # filter by frame
    #                 b_time: {
    #                     '$lte': blob_a[a_time] + (0 if reverse else MAX_FRAME_GAP),
    #                     '$gte': blob_a[a_time] - (MAX_FRAME_GAP if reverse else 0),
    #                     },
    #                 # filter by distance (this will rough out a cylinder, need 
    #                 # further scuplting to get our desired cone)
    #                 b_coord: {'$within': {
    #                     '$center': [blob_a[a_coord], MAX_DIST / MONGO_GEO_SCALE],
    #                     }},
    #             }, b_fields):
    #             f_gap = abs(blob_b[b_time] - blob_a[a_time])
    #             d_gap = dist(blob_a[a_coord], blob_b[b_coord]) * MONGO_GEO_SCALE
    #             if (d_gap <= WORM_ERROR + f_gap * MAX_WORM_SPEED/MAX_OBS_FRAC):
    #                 # a->b is possible, save it.
    #                 logger.debug("{} -> {}".format(blob_a['bid'], blob_b['bid']))
    #                 if extended:
    #                     candidates[blob_a['bid']].append({
    #                             'bid': blob_b['bid'], 
    #                             'd': d_gap, 
    #                             'f': f_gap,
    #                         })
    #                 else:
    #                     candidates[blob_a['bid']].append(blob_b['bid'])

    #     if len(candidates) <= 0:
    #         print('Warning: No data.')

    #     candidates['reverse'] = reverse

    #     if dumpfile:
    #         with open(dumpfile, 'wb') as f:
    #             pickle.dump(candidates, f)

    #     return candidates
