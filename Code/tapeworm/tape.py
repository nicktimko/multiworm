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

def dist(a, b):
    '''
    Reurns the Euclidean distance between *a* and *b*.
    '''
    return np.linalg.norm(np.array(a) - np.array(b))

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

    def _allocate_zeros(self, width, dtype=None):
        return np.zeros((self.plate.max_blobs, width), dtype=dtype)

    def load_data(self, show_progress=False):
        """
        Call to load data from the experiment and set up scoring method
        """
        self.plate.load_summary()
        self.starts = self._allocate_zeros(4, dtype='int32')
        self.ends = self._allocate_zeros(4, dtype='int32')
        self.displacements = self._allocate_zeros(self.horizon_frames)

        for i, blob in enumerate(itertools.islice(self.plate.good_blobs(), 7)):
            bid, bdata = blob
            bdata = self._condense_blob(bdata)
            blob = None

            self.starts[i] = (bid,) + bdata['born_at'] + (bdata['born_f'],)
            self.ends[i] = (bid,) + bdata['died_at'] + (bdata['died_f'],)
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

    def find_candidates(self, max_fgap=500, max_dgap=400):
        """
        Finds all candidate joins within the given number of frames and 
        distance.
        """
