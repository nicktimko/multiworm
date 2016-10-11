from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import unittest

import multiworm


TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'
SYNTH1 = DATA_DIR / 'synth1'


class TestExperimentOpen(unittest.TestCase):

    def test_pathlib(self):
        ex = multiworm.Experiment(SYNTH1)

    def test_strpath(self):
        ex = multiworm.Experiment(str(SYNTH1))

    def test_root_and_id(self):
        ex = multiworm.Experiment(
            data_root=DATA_DIR,
            experiment_id='synth1',
        )

    def test_strroot_and_id(self):
        ex = multiworm.Experiment(
            data_root=str(DATA_DIR),
            experiment_id='synth1',
        )


class TestMalformedExperiments(unittest.TestCase):

    def test_nonexistent_folder(self):
        try:
            ex = multiworm.Experiment(DATA_DIR / 'guaranteedtohopefullynotexist')
        except multiworm.core.MWTDataError:
            self.fail('Overly specific error raised')
        except IOError as e:
            pass
        else:
            self.fail("Didn't even mention the folder isn't there")

    def test_missing_summary(self):
        try:
            ex = multiworm.Experiment(DATA_DIR / 'bad_empty')
        except multiworm.core.MWTDataError as e:
            pass
        else:
            self.fail("Didn't raise error despite no summary file")

    def test_dupe_summary(self):
        try:
            ex = multiworm.Experiment(DATA_DIR / 'bad_twosummary')
        except multiworm.core.MWTSummaryError as e:
            pass
        else:
            self.fail("Didn't raise error with ambiguous summary file")


class TestMalformedData(unittest.TestCase):

    def test_zero_frame(self):
        try:
            ex = multiworm.Experiment(DATA_DIR / 'bad_framezero')
        except multiworm.core.MWTDataError:
            pass
        else:
            self.fail("Didn't raise error on malformed data with a frame 0")


class TestReadingData(unittest.TestCase):

    def setUp(self):
        self.ex = multiworm.Experiment(SYNTH1)

    def test_length_is_num_blobs(self):
        self.assertEqual(11, len(self.ex))

    def test_iter(self):
        count = 0
        for thing in self.ex:
            count += 1
        self.assertEqual(11, count)

    def test_iter_blobs(self):
        count = 0
        for thing in self.ex.blobs():
            count += 1
        self.assertEqual(11, count)
