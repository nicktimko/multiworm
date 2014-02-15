# -*- coding: utf-8 -*-
"""
Generic Python manipulations.  No MWT things.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

def multifilter(filters, iterable):
    """
    Like the builtin filter(), but takes an iterable of functions for the 
    first argument.
    """
    for f in filters:
        iterable = filter(f, iterable)
    return iterable

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
