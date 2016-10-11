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

SYNTH1_N_BLOBS = 12


class TestBlobAccess(unittest.TestCase):

    def setUp(self):
        self.ex = multiworm.Experiment(SYNTH1)
        self.blob = self.ex[1]

    def test_blob_is_blob_object(self):
        self.assertIsInstance(self.blob, Blob)

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


# class TestBlobAccessPartial(unittest.TestCase):
#
#     def setUp(self):
#         self.ex = multiworm.Experiment(SYNTH1)
#
#     def test_partial(self):
#         blob = self.ex[1]
#         blob.crop([])


class TestBlobProperties(unittest.TestCase):

    def setUp(self):
        self.ex = multiworm.Experiment(SYNTH1)

    def test_blob_empty(self):
        blob = self.ex[12]
        self.assertTrue(blob.empty)

    def test_blob_empty_df(self):
        blob = self.ex[12]
        df = blob.df
        self.assertIs(df, None)
