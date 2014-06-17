#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lazy views into blobs
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

class Blob(object):
    def __init__(self, experiment, blob_id):
        self.experiment = experiment
        self.blob_id = blob_id
        self.summary_data = self.experiment.summary_data(self.blob_id)
        self.blob_data = None

    def __getitem__(self, key):
        try:
            return self.summary_data[key]
        except LookupError:
            if self.blob_data is None:
                self.blob_data = self.experiment.parse_blob(self.blob_id)
            return self.blob_data[key]
