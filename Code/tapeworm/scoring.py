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
import matplotlib.pyplot as plt

KDE_SAMPLES = 500 #: Default number of samples to take along KDE distribution

class DisplacementScorer(object):
    def __init__(self, displacements):
        self.kde_fit(displacements)

        self.show()

    def kde_fit(self, displacements, bandwidth=None, subsample=None, samples=KDE_SAMPLES):
        frame_gaps = np.arange(1, displacements.shape[1], subsample)
        distances = np.linspace(0, displacements.max(), samples)
        self.scores = np.empty((frame_gaps.size, distances.size))

        #import pdb;pdb.set_trace()
        for i, dist in enumerate(displacements.T[1:]):
            self.scores[i] = sps.gaussian_kde(dist, bandwidth)(distances)

        print(self.scores)

        self.distance_domain = 0, displacements.max()
        self.frame_gap_domain = 1, len(displacements)
        self.score_interp = spi.RectBivariateSpline(frame_gaps, distances, self.scores)

    def show(self):
        fig, ax = plt.subplots()
        #colormap = plt.cm.gist_ncar
        #ax.set_color_cycle([colormap(i) for i in 
        #        np.linspace(0, 0.9, len(self.displacements))])

        #for row in self.displacements:
        #    plt.plot(row)

        dgap = np.linspace(*self.distance_domain)
        fgap = np.linspace(*self.frame_gap_domain)
        dgap_v, fgap_v = np.meshgrid(dgap, fgap)

        score = self(dgap_v, fgap_v)
        print(score)

        #plt.show()


    def __call__(self, dgap, fgap):
        return self.score_interp(dgap, fgap)
