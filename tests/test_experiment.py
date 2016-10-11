from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import unittest

import networkx as nx

import multiworm


TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'
SYNTH1 = DATA_DIR / 'synth1'

SYNTH1_N_BLOBS = 12


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

    def test_empty_fail(self):
        try:
            multiworm.Experiment()
        except Exception as e:
            if not isinstance(e, ValueError):
                self.fail('raised some unexpected error')
            if not all(x in str(e) for x in ['experiment_id', 'must', 'provided']):
                self.fail('error message unexpected')
        else:
            self.fail('experiment constructor worked with no arguments')

    def test_dataroot_only_fail(self):
        try:
            multiworm.Experiment(data_root=DATA_DIR)
        except Exception as e:
            if not isinstance(e, ValueError):
                self.fail('raised some unexpected error')
            if not all(x in str(e) for x in ['experiment_id', 'must', 'provided']):
                self.fail('error message unexpected')
        else:
            self.fail('experiment constructor allowed data-root only without erroring')

    def test_custom_id(self):
        my_id = 'peterspeppers'
        ex = multiworm.Experiment(fullpath=SYNTH1, experiment_id=my_id)
        self.assertEquals(ex.id, my_id)

    def test_callback(self):
        class StateThing(object):
            def __init__(self):
                self.progress = -1

            def __call__(self, progress):
                assert progress >= self.progress
                self.progress = progress

        ex = multiworm.Experiment(SYNTH1, callback=StateThing())


class TestMalformedExperiments(unittest.TestCase):

    def test_nonexistent_folder(self):
        try:
            ex = multiworm.Experiment(DATA_DIR / 'guaranteedtohopefullynotbethere')
        except multiworm.core.MWTDataError:
            self.fail('Overly specific error raised')
        except IOError as e:
            self.assertIn('exist', str(e))
        else:
            self.fail("Didn't even mention the folder isn't there")

    def test_check_is_dir(self):
        try:
            ex = multiworm.Experiment(SYNTH1 / 'test_blobsfile.png')
        except multiworm.core.MWTDataError:
            self.fail('Overly specific error raised')
        except IOError as e:
            self.assertIn('directory', str(e))
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
        self.assertEqual(SYNTH1_N_BLOBS, len(self.ex))

    def test_iter(self):
        count = 0
        for thing in self.ex:
            count += 1
        self.assertEqual(SYNTH1_N_BLOBS, count)

    def test_iter_blobs(self):
        count = 0
        for thing in self.ex.blobs():
            count += 1
        self.assertEqual(SYNTH1_N_BLOBS, count)


class TestExperimentProperties(unittest.TestCase):

    def setUp(self):
        self.ex = multiworm.Experiment(SYNTH1)

    def test_blobs_in_frame(self):
        self.assertEquals(list(self.ex.blobs_in_frame(10)), list(range(1, 12)))
        self.assertEquals(list(self.ex.blobs_in_frame(200)), list(range(5, 12)))

    def test_locked_graph(self):
        try:
            self.ex.graph.add_node(123)
        except nx.NetworkXError as e:
            self.assertIn('frozen', str(e).lower())
        else:
            self.fail('experiment graph should be frozen/locked')

    def test_graph_copy_unlocked(self):
        G = self.ex.graph.copy()
        G.add_node(123)
        G.add_edge(55, 66)
