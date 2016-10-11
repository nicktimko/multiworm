from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import inspect
import pathlib
import unittest

import multiworm
import multiworm.readers.summary as mrs

from change_defaults import change_defaults

TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'
SYNTH1 = DATA_DIR / 'synth1'


class TestSummaryGrowing(unittest.TestCase):

    def test_grow(self):
        """Manipulate the function defaults for the 'dynamic' numpy array to
        force it to reallocate once or twice."""
        summary, _ = mrs.find(SYNTH1)

        with change_defaults(mrs.init_array, rows=2):
            mrs.parse(summary)
