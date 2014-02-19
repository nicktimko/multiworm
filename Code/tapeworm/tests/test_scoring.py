import unittest

import numpy as np

import tapeworm.scoring

class TestScoring(unittest.TestCase):

    def setUp(self):
        np.random.seed(0)
        self.length = 30
        self.n_paths = 20
        offset = 0.8
        self.displacement_data = np.array([
                0.2 * (np.random.rand() + 0.5) # some random scaling
                * np.append([0], # start at 0
                    np.cumsum(np.random.rand(self.length - 1) + offset)) 
                for _ in range(self.n_paths)
            ])
        self.max_displacement = self.displacement_data.max()

    def test_fitter(self):
        scorer = tapeworm.scoring.DisplacementScorer(self.displacement_data)
        self.assertEquals(tuple(scorer.frame_gap_domain), (1, self.length))
        self.assertEquals(tuple(scorer.distance_domain), (0, self.max_displacement))

        try:
            scorer(1, 0) # 1 frame, no displacement
            scorer(self.length / 2, self.max_displacement / 2)
            scorer(self.length, self.max_displacement)
        except ValueError:
            self.fail("Domain error when calling scorer")

        bad_args = [
                (self.length + 0.1, self.max_displacement / 2),
                (self.length / 2, self.max_displacement + 0.1),
                (-0.1, self.max_displacement / 2),
                (self.length / 2, -0.1)
            ]
        for badness in bad_args:
            self.assertRaises(ValueError, scorer, *badness)


if __name__ == '__main__':
    unittest.main()
