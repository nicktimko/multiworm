from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import unittest

import multiworm


TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'

GOOD = DATA_DIR / '00000000_000001'

class TestExperimentOpen(unittest.TestCase):

    def test_pathlib(self):
        path = GOOD
        assert isinstance(path, pathlib.Path)
        ex = multiworm.Experiment(path)

    def test_strpath(self):
        path = str(GOOD)
        assert isinstance(path, str)
        ex = multiworm.Experiment(path)
