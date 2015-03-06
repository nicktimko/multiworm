# -*- coding: utf-8 -*-
"""
Generic Python manipulations.  No MWT things.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import numpy as np
import pandas as pd

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


PREALLOC_ROWS = 1000

class DataFramePreallocator(object):
    def __init__(self, fill, columns, chunk_size=PREALLOC_ROWS):
        self.fill = fill
        self.columns = columns
        self.chunk_size = chunk_size
        self.chunks = {}

    def __getitem__(self, idx):
        chunk = self._get_chunk(idx)
        return chunk.loc[idx]

    def __setitem__(self, key, val):
        idx, col = key
        chunk = self._get_chunk(idx)
        chunk.loc[key] = val

    def _get_chunk(self, idx):
        chunk_number = idx // self.chunk_size
        if chunk_number not in self.chunks:
            self.chunks[chunk_number] = self._new_df(chunk_number)

        return self.chunks[chunk_number]

    def _new_df(self, chunk_number):
        index = range(PREALLOC_ROWS * chunk_number, PREALLOC_ROWS * (chunk_number + 1))
        return pd.DataFrame([self.fill], columns=self.columns, index=index)

    def flatten(self):
        """Return a basic dataframe"""
        return pd.concat(self.chunks.values())


class ArrayAutoAllocator(object):
    def __init__(self, n_columns, fill_val=-1, chunk_size=PREALLOC_ROWS, dtype=None):
        self.n_columns = n_columns + 1 # for the index
        self.fill_val = fill_val
        self.chunk_size = chunk_size
        self.dtype = dtype
        self.chunks = {}

    def __getitem__(self, idx):
        chunk = self._get_chunk(idx)
        return chunk[idx]

    def __setitem__(self, key, val):
        idx, col = key
        chunk = self._get_chunk(idx)
        chunk[idx % self.chunk_size, col] = val

    def _get_chunk(self, idx):
        chunk_number = idx // self.chunk_size
        if chunk_number not in self.chunks:
            self.chunks[chunk_number] = self._new_array(chunk_number)

        return self.chunks[chunk_number]

    def _new_array(self, chunk_number):
        a = self.fill_val * np.ones((self.chunk_size, self.n_columns), dtype=self.dtype)
        a[...,0] = np.arange(self.chunk_size * chunk_number, self.chunk_size * (chunk_number + 1))
        return a

    def flatten(self):
        """Return a basic array"""
        S = self.chunk_size
        total = np.empty((S * len(self.chunks), self.n_columns), dtype=self.dtype)
        for i, cn in enumerate(sorted(self.chunks.keys())):
            total[S*i:S*(i+1)] = self.chunks[cn]
        return total

    def crush(self):
        total = self.flatten()
        bool_filt = np.sum(total[...,1:], axis=1) != (self.n_columns - 1) * self.fill_val
        return total[bool_filt]
