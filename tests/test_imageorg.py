from __future__ import absolute_import, division, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import unittest
import warnings

import multiworm
import multiworm.readers.image as mwimg


TEST_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_ROOT / 'data'
SYNTH1 = DATA_DIR / 'synth1'

SYNTH1_IMAGES_MS = [
    '0',
    # used the below to generate numbers to stick into the filename (the 0
    # above is special because that .png has no number at all)

    # random.seed(1)
    # images = [random.random() * 120 for _ in range(20)]
    # images.extend(0.99 * 10 ** x for x in range(-2, 3))
    # images.extend(1.00 * 10 ** x for x in range(-2, 3))
    # images.sort()
    # images = [format(int(1000 * x), 'd') for x in images]

    '9',
    '10',
    '99',
    '100',
    '252',
    '990',
    '1000',
    '3401',
    '3670',
    '9900',
    '10000',
    '11263',
    '16123',
    '27451',
    '30608',
    '51932',
    '53446',
    '53938',
    '59452',
    '78191',
    '86584',
    '91473',
    '91652',
    '94646',
    '99000',
    '100000',
    '100291',
    '101692',
    '108171',
    '113432',
]


class TestImageFinding(unittest.TestCase):

    def test_finding(self):
        basename = 'test_blobsfile'
        found = mwimg.find(
            directory=SYNTH1,
            basename=basename,
        )

        # converting the floats to ms then rounding is hopefully robust
        # against any imprecise float nastiness
        times = sorted(found.keys())
        ms_rounded = [str(int(round(1000 * t))) for t in times]
        self.assertEqual(
            ms_rounded,
            SYNTH1_IMAGES_MS,
        )

    def test_existance(self):
        basename = 'test_blobsfile'
        found = mwimg.find(
            directory=SYNTH1,
            basename=basename,
        )

        for path in found.values():
            assert path.exists()
            assert path.is_file()


class ArbitraryShim(object):
    pass


class TestImageOrganizer(unittest.TestCase):

    def setUp(self):
        ex = ArbitraryShim()
        #                  1    2     3....
        ex.frame_times = [0.0, 0.04, 0.08, 0.16, 0.19, 0.2, 0.25, 0.3, 0.35, 0.4]

        self.entries = [
            (0.1, 'a'),
            (0.2, 'b'),
            (0.3, 'c'),
        ]
        self.ifo = mwimg.ImageFileOrganizer(dict(self.entries), experiment=ex)

    def assertSameEntry(self, got, expected=None, eix=None):
        if expected is None:
            expected = self.entries[eix]

        self.assertEqual(got[0], expected[1])
        self.assertAlmostEqual(got[1], expected[0])

    def test_nearest_time_up(self):
        self.assertSameEntry(self.ifo.nearest(time=0), eix=0)

    def test_nearest_time_down(self):
        self.assertSameEntry(self.ifo.nearest(time=0.4), eix=2)

    def test_nearest_time_mid_up(self):
        self.assertSameEntry(self.ifo.nearest(time=0.0501), eix=0)

    def test_nearest_time_mid_down(self):
        self.assertSameEntry(self.ifo.nearest(time=0.2499), eix=1)

    def test_nearest_frame_up(self):
        self.assertSameEntry(self.ifo.nearest(frame=0), eix=0)

    def test_nearest_frame_down(self):
        self.assertSameEntry(self.ifo.nearest(frame=9), eix=2)

    def test_nearest_frame_mid_up(self):
        self.assertSameEntry(self.ifo.nearest(frame=4), eix=1)

    def test_nearest_frame_mid_down(self):
        self.assertSameEntry(self.ifo.nearest(frame=3), eix=0)

    def test_nearest_frame_complains_float(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            self.ifo.nearest(frame=2.5)

            assert len(w) == 1
            assert "non-integer" in str(w[-1].message)

    def test_nearest_frame_no_complains_inty_float(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            self.ifo.nearest(frame=2.0)

            assert len(w) == 0

    def test_nearest_no_kwargs(self):
        self.assertRaisesRegexp(ValueError, 'either', self.ifo.nearest)

    def test_spanning_frame_at_least_1(self):
        assert len(self.ifo.spanning(frame=[0, 2])) == 1
        assert len(self.ifo.spanning(frame=[9, 10])) == 1

    def test_spanning_time_at_least_1(self):
        assert len(self.ifo.spanning(time=[0.35, 1])) == 1
        assert len(self.ifo.spanning(time=[100, 2000])) == 1

    def test_spanning_frame_errors_not_2(self):
        self.assertRaisesRegexp(ValueError, 'two', self.ifo.spanning, frame=[0])
        self.assertRaisesRegexp(ValueError, 'two', self.ifo.spanning, frame=[1, 2, 3])

    def test_spanning_time_errors_not_2(self):
        self.assertRaisesRegexp(ValueError, 'two', self.ifo.spanning, time=[0.1])
        self.assertRaisesRegexp(ValueError, 'two', self.ifo.spanning, time=[0.11, 0.22, 0.33])
