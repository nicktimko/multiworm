#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lazy views into blobs
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import collections

import numpy as np
import pandas as pd

from .readers.blob import decode_outline
from .readers.summary import NO_DATA
from .util import lazyprop, LAZY_PREFIX

SERIES_FIELDS = [
    'frame',
    'time',
    'centroid',
    'area',
    'std_vector',
    'std_ortho',
    'size',
    'midline',
    'contour_start',
    'contour_encode_len',
    'contour_encoded',
]

class BlobDataFrame(pd.DataFrame):

    CONTOUR_COLUMNS = ['contour_start', 'contour_encode_len', 'contour_encoded']

    def decode_contour(self):
        if 'contour' in self:
            # already created; no-op.
            return
        self['contour'] = self.apply(self._contour_decoder, axis=1)
        self.drop(self.CONTOUR_COLUMNS, axis=1, inplace=True)

    @classmethod
    def _contour_decoder(cls, series):
        start, length, enc = series[cls.CONTOUR_COLUMNS]
        if not length or not np.isfinite(length):
            return None

        return decode_outline(start, length, enc).tolist()


class Blob(collections.Mapping):
    def __init__(self, experiment, blob_id, fields=None):
        self.experiment = experiment
        self.id = blob_id

        self.summary_data = self.experiment.summary_data(self.id)
        self.blob_data = None

        if self.summary_data['file_no'] == NO_DATA:
            setattr(self, LAZY_PREFIX + 'empty', True)

        self.crop(fields)

    def __repr__(self):
        return '<Blob {} of Experiment {}>'.format(self.id, self.experiment.id)

    def __len__(self):
        return len(self.fields)

    def __iter__(self):
        return iter(self.fields)

    def __getitem__(self, key):
        try:
            return self.summary_data[key]
        except LookupError:
            if self.empty:
                return []

            if self.blob_data is None:
                self.blob_data = self.experiment._parse_blob(self.id)

            return self.blob_data[key]

    def __getattr__(self, name):
        try:
            return self.summary_data[name]
        except LookupError:
            raise AttributeError("'Blob' object has no attribute '{}'".format(name))

    def crop(self, fields):
        """
        Limit the keys that are iterated through. Perhaps useful if you
        don't want to load as much stuff into a DataFrame.
        """
        if fields is None:
            self.fields = SERIES_FIELDS[:]
        else:
            self.fields = fields

        return self # chainable

    def raw_lines(self):
        """
        Yield raw lines from the blobs files
        """
        for line in self.experiment._blob_lines(self.id):
            yield line

    @lazyprop
    def empty(self):
        """
        Check if the blob really contains any data

            "Tommy, how's the peeping? Tommy. How's the peeping?
            Tommy. Tommy. Tommy. Tommy. Tommy."

                                           -- Freddie Miles
        """
        gen = self.experiment._blob_lines(self.id)

        try:
            next(gen)
        except (StopIteration, ValueError):
            # - StopIteration raised on a zero-line blob
            # - ValueError raised on a blob that isn't even denoted anywhere
            #       in the blobs files (readers.summary.NO_DATA in the
            #       summary data)
            return True

        return False

    @lazyprop
    def df(self):
        """
        Loads the fields from a blob in the provided experiment and converts
        to a dataframe.
        """
        if self.empty:
            return None
        return BlobDataFrame(dict(self.experiment[self.id]))
