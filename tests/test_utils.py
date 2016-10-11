from __future__ import absolute_import, print_function, unicode_literals
import six
from six.moves import zip, filter, map, reduce, input, range

import pathlib
import time
import unittest

import multiworm


class TestMultiFilter(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.multifilter

    def ne2(self, x):
        return x != 2

    def neSTR(self, x):
        return x != 'str'

    def test_zero(self):
        inputs = ['a', 'b', 0xC, 1, 2, int, str, 'str', None]
        outputs = list(self.f([], inputs))
        self.assertEqual(inputs, outputs)

    def test_one(self):
        inputs = ['a', 'b', 0xC, 1, 2, int, str, 'str', None]
        filters = [self.ne2]

        outputs = list(self.f(filters, inputs))

        expected = ['a', 'b', 0xC, 1, int, str, 'str', None]
        self.assertEqual(expected, outputs)

    def test_two(self):
        inputs = ['a', 'b', 0xC, 1, 2, int, str, 'str', None]
        filters = [self.ne2, self.neSTR]

        outputs = list(self.f(filters, inputs))

        expected = [x for x in inputs if all([self.ne2(x), self.neSTR(x)])]
        self.assertEqual(expected, outputs)

    def test_returns_lazy_generator(self):
        gut = self.f([self.ne2], [1, 2, 3])

        assert hasattr(gut, '__iter__')
        assert not hasattr(gut, '__getitem__')
        assert not hasattr(gut, '__len__')


class TestMultiTransform(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.multitransform

    def one(self, x):
        return x + 1

    def two(self, x):
        return x * 2

    def test_one_transform(self):
        x = 1
        transforms = [self.one]

        y = self.f(transforms, x)

        expected = self.one(x)
        self.assertEqual(expected, y)

    def test_two_transforms(self):
        x = 1
        transforms = [self.one, self.two]

        y = self.f(transforms, x)

        expected = self.two(self.one(x))
        self.assertEqual(expected, y)


class TestAlternate(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.alternate

    def test_basic(self):
        x = list(range(10))
        a, b = self.f(x)
        self.assertEqual(a, [0, 2, 4, 6, 8])
        self.assertEqual(b, [1, 3, 5, 7, 9])


class TestDtype(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.dtype

# def dtype(spec):
#     """
#     Allow Python 2/3 compatibility with Numpy's dtype argument.
#
#     Relevant issue: https://github.com/numpy/numpy/issues/2407
#     """

class TestEnumerate(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.enumerate

    def test_basic(self):
        seq = range(5)
        nn = []
        xx = []

        for n, x in self.f(seq):
            nn.append(n)
            xx.append(x)

        self.assertEqual(nn, xx)

    def test_other_start(self):
        seq = range(5)
        start = 100
        nn = []
        xx = []

        for n, x in self.f(seq, start=start):
            nn.append(n)
            xx.append(x)

        self.assertEqual([n - start for n in nn], xx)

    # def test_releases_handle(self):
    #     'how to do this...'


class TestLazyProp(unittest.TestCase):
    def setUp(self):
        self.f = multiworm.util.lazyprop

    def test_caching(self):
        class A(object):
            @self.f
            def b(self):
                time.sleep(0.2)
                return 'red stapler'

        a = A()
        tick = time.time()
        assert a.b == 'red stapler'
        assert time.time() - tick > 0.15

        tick = time.time()
        assert a.b == 'red stapler'
        assert time.time() - tick < 0.05
