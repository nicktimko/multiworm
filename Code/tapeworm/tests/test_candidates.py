from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)
import unittest
import math

import numpy as np

from multiworm.util import dtype
import tapeworm.tape

terminal_fields = dtype([('bid', 'int32'), ('loc', '2int16'), ('f', 'int32')])
def termini(data):
    return np.array(data, terminal_fields)

class TestCandidateFinding(unittest.TestCase):

    def setUp(self):
        pass

    def test_basic(self):
        ends = termini([(1, (100, 100), 10)])
        starts = termini([(2, (100, 100), 20)])
        self.assertEqual(tapeworm.tape.find_candidates(ends, starts), {1:{2:{'f':10, 'd': 0}}})

    def test_causality(self):
        ends = termini([(1, (100, 100), 100)])
        startses = [
                termini([(2, (100, 100), 100)]),
                termini([(2, (100, 100), 99)]),
                termini([(2, (200, 100), 100)]),
            ]
        for starts in startses:
            self.assertEqual(tapeworm.tape.find_candidates(ends, starts), {1:{}})

    def test_cone(self):
        ends = termini([(1, (100, 100), 100)])
        params = {'error': 0, 'max_speed': 1, 'max_fgap': 1000}
        
        # inside the cone
        insides = [
            [(2, (100, 100), 101)],
            [(3, (100, 100), 101)],
            [(4, (200, 100), 200)],
        ]

        for starts in insides:
            starts = termini(starts)
            expected_result = {1: {starts['bid'][0]: {
                    'f': starts['f'] - ends['f'], 
                    'd': math.sqrt(
                            (starts['loc'][0][0] - ends['loc'][0][0])**2
                            + (starts['loc'][0][1] - ends['loc'][0][1])**2)
                }}}
            self.assertEqual(tapeworm.tape.find_candidates(
                    ends, termini(starts), params=params),
                expected_result,
            )

        # outside the cone
        outsides = [
            [(2, (200, 100), 199)],
            [(3, (400, 500), 599)],
            [(4, (100, 100), 1101)],
        ]

        for starts in outsides:
            self.assertEqual(tapeworm.tape.find_candidates(
                    ends, termini(starts), params=params),
                {1:{}},
            )

    def test_multiple(self):
        params = {'error': 0, 'max_speed': 1, 'max_fgap': 1000}

        ends = termini([
                (1, (100, 100), 100),
                (2, (100, 500), 200),
            ])
        starts = termini([
                (10, (400, 500), 500),
                (20, (400, 100), 1000),
            ])

        expected_result = {
            1: {
                #10: {'f': 400, 'd': 500}, # too fast, d/f > 1
                20: {'f': 900, 'd': 300},
            },
            2: {
                10: {'f': 300, 'd': 300},
                20: {'f': 800, 'd': 500},
            },
        }

        self.assertEqual(
                tapeworm.tape.find_candidates(ends, starts, params=params),
                expected_result,
            )
