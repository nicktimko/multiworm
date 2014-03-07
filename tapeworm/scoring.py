#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generates a scoring function from worm data that can be fed a time and 
distance gap to predict connected worm tracks.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import numpy as np
import scipy.stats as sps
import scipy.interpolate as spi
#import matplotlib.pyplot as plt

KDE_SAMPLES = 1000 #: Default number of samples to take along KDE distribution

class DisplacementScorer(object):
    def __init__(self, displacements, *args, **kwargs):
        self.kde_fit(displacements, *args, **kwargs)

        #self.show()

    def kde_fit(self, displacements, bandwidth=None, subsample=None, 
            samples=KDE_SAMPLES):
        # if subsample is None:
        #     subsample = 1

        #self.distance_domain = 0, np.percentile(displacements[-1], 95)
        self.distance_domain = 0, displacements.compressed().max()

        # -1 on the shape because we're given the useless first frame (all 0's)
        self.frame_gap_domain = 1, displacements.shape[1] - 1

        distances = np.linspace(*self.distance_domain, num=samples)
        frame_gaps = np.arange(self.frame_gap_domain[0], 
                self.frame_gap_domain[1] + 1, step=subsample)

        self.scores = np.empty((frame_gaps.size, distances.size))

        #for i, dist in enumerate(displacements.T[1:]):
        for i, fgap in enumerate(frame_gaps):
            dist = displacements[:,fgap].compressed()
            self.scores[i] = sps.gaussian_kde(dist, bandwidth)(distances)

        self.score_interp = spi.RectBivariateSpline(frame_gaps, distances, self.scores)

    # def show(self):
    #     fig, ax = plt.subplots()
    #     #colormap = plt.cm.gist_ncar
    #     #ax.set_color_cycle([colormap(i) for i in 
    #     #        np.linspace(0, 0.9, len(self.displacements))])

    #     #for row in self.displacements:
    #     #    plt.plot(row)

    #     dgap = np.linspace(*self.distance_domain, num=400)
    #     fgap = np.linspace(*self.frame_gap_domain, num=400)
    #     #fgap_v, dgap_v = np.meshgrid(fgap, dgap, squeeze=True)
    #     #import pdb;pdb.set_trace()

    #     score = self(fgap, dgap)
    #     ax.imshow(score)
    #     #print(score)

    #     #plt.show()

    def __call__(self, fgap, dgap):
        """
        Interface to the interpolater.
        """
        result = self.score_interp(fgap, dgap)
        return np.clip(result, 1e-100, 1e100, out=result)
