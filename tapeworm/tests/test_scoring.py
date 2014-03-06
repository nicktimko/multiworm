from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import unittest

import numpy as np

import tapeworm.scoring

class TestScoring(unittest.TestCase):

    def setUp(self):
        np.random.seed(0)
        self.length = 30
        self.n_paths = 20
        offset = 0.8
        displacement_data = np.array([
                0.2 * (np.random.rand() + 0.5) # some random scaling
                * np.append([0], # start at 0
                    np.cumsum(np.random.rand(self.length - 1) + offset)) 
                for _ in range(self.n_paths)
            ])

        self.min_f, self.max_f = (1, self.length)
        self.min_d, self.max_d = (0, displacement_data.max())
        self.mean_f = (self.min_f + self.max_f) / 2
        self.mean_d = (self.min_d + self.max_d) / 2

        self.scorer = tapeworm.scoring.DisplacementScorer(displacement_data)

    def test_internal_domain(self):
        self.assertEquals(
                tuple(self.scorer.frame_gap_domain),
                (self.min_f, self.max_f),
                "Scorer frame gap domain differs from expected value.")
        self.assertEquals(
                tuple(self.scorer.distance_domain),
                (self.min_d, self.max_d),
                "Scorer distance gap domain differs from expected value.")

    def test_good_values(self):
        # Validate domain and range
        args = [
            # corners
            (self.min_f, self.min_d),
            (self.max_f, self.min_d),
            (self.min_f, self.max_d),
            (self.max_f, self.max_d),
            # edges
            (self.mean_f, self.min_d),
            (self.mean_f, self.max_d),
            (self.min_f, self.mean_d),
            (self.max_f, self.mean_d),
            # middle
            (self.mean_f, self.mean_d),
        ]
        for arg in args:
            self.assertTrue(1e-100 <= self.scorer(*arg), 
                    "Scorer returning values that are too small/negative "
                    "in domain.")

    def test_bad_values(self):
        bad_args = [
                (self.max_f + 0.1, self.mean_d),
                (self.mean_d, self.max_d + 0.1),
                (self.min_f - 0.1, self.mean_d),
                (self.mean_f, self.min_d - 0.1),
            ]
        for badness in bad_args:
            self.assertTrue(self.scorer(*badness) >= 0,
                    "Scorer accepting values in known-bad domain")

if __name__ == '__main__':
    unittest.main()
