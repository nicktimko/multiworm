# -*- coding: utf-8 -*-
"""
Generic Python manipulations.  No MWT things.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

LAZY_PREFIX = '_lazy_'

def multifilter(filters, iterable):
    """
    Like the builtin filter(), but takes an iterable of functions for the
    first argument.
    """
    for f in filters:
        iterable = filter(f, iterable)
    return iterable

def multitransform(transforms, data):
    """
    Transforms *data* by passing it through all functions in *transforms*,
    in order.
    """
    return reduce(lambda x, f: f(x), transforms, data)

def alternate(seq):
    """
    Splits *seq*, placing alternating values into the returned iterables
    """
    return seq[::2], seq[1::2]

def dtype(spec):
    """
    Allow Python 2/3 compatibility with Numpy's dtype argument.

    Relevant issue: https://github.com/numpy/numpy/issues/2407
    """
    if six.PY2:
        return [(str(n), str(t) if type(t)==type else t) for n, t in spec]
    else:
        return spec

def enumerate(sequence, start=0):
    """
    A version of the built-in enumerate that doesn't hold item references,
    permitting up to 2x lower memory use.
    """
    n = start
    sequence = iter(sequence)
    while True:
        yield n, six.next(sequence)
        n += 1

def lazyprop(fn):
    """http://stackoverflow.com/a/3013910/194586"""
    attr_name = LAZY_PREFIX + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop
