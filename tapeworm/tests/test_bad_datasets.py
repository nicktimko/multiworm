from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import unittest

import numpy as np
import tapeworm.scoring
from tapeworm.core import OneGoodBlobException

class TestBadDatasets(unittest.TestCase):

    def setUp(self):
        np.random.seed(1)

    def test_one_good_blob(self):
        self.length = 30
        self.n_paths = 1
        offset = 0.8
        displacement_data = np.ma.array([
                0.2 * (np.random.rand() + 0.5) # some random scaling
                * np.append([0], # start at 0
                    np.cumsum(np.random.rand(self.length - 1) + offset)) 
                for _ in range(self.n_paths)
            ])

        self.min_f, self.max_f = (1, self.length - 1)
        self.min_d, self.max_d = (0, displacement_data.max())
        self.mean_f = (self.min_f + self.max_f) / 2
        self.mean_d = (self.min_d + self.max_d) / 2

        try:
            self.scorer = tapeworm.scoring.DisplacementScorer(displacement_data)
        except OneGoodBlobException:
            pass
        except ValueError:
            self.fail("Uncaptured ValueError exception when trying to "
                      "construct scoring model with single trace.")
        else:
            self.fail("Scorer allowed construction of model using a single trace.")


if __name__ == '__main__':
    unittest.main()
