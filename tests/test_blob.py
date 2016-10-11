from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import unittest

import multiworm
from multiworm.blob import Blob


TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'
SYNTH1 = DATA_DIR / 'synth1'


class TestBlobAccess(unittest.TestCase):

    def setUp(self):
        ex = multiworm.Experiment(SYNTH1)
        self.blob = ex[1]

    def test_blob_is_blob_object(self):
        self.assertIsInstance(self.blob, Blob)

    # def test_blob_len(self):
    #     self.assertEqual(, len(self.blob))

    def test_dataframe_access(self):
        df = self.blob.df

    def test_contour_decoding(self):
        df = self.blob.df

        self.assertNotIn('contour', df)
        df.decode_contour()
        self.assertIn('contour', df)

    def test_cached_contours(self):
        df = self.blob.df

        df.decode_contour()
        before = set(df.columns)
        df.decode_contour()
        after = set(df.columns)

        self.assertEqual(before, after)
