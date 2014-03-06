#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handles data from a Multi-Worm Tracker experiment
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os.path
from collections import defaultdict
import glob
import re

import numpy as np

from .readers import blob, summary
from .util import multifilter, multifilter_block, MWTDataError


class Experiment(object):
    """
    Provides interfaces for Multi-Worm Tracker experiment data.

    Provide the path to the experiment data in order to initialize.  Next, 
    pass filter functions to :func:`add_summary_filter` and/or 
    :func:`add_filter`.  Then call :func:`load_summary` to index the 
    location of all possible good blobs.
    """
    def __init__(self, data_path):
        self.data_path = data_path
        self._find_summary_file()
        self._find_blobs_files()
        self._find_images()

        self.blobs_summary = None
        
        self.summary_filters = []
        self.filters = []

        # Upper bound of how many blobs there will be (for array
        # preallocation)
        self.max_blobs = None

        self.blobs_parsed = 0

    def _find_summary_file(self):
        """
        Find blobs files and verify uniqueness
        """
        try:
            summaries = glob.glob(os.path.join(self.data_path, '*.summary'))
            if len(summaries) > 1:
                raise MWTDataError("Multiple summary files in target path.")
            self.summary = summaries[0]
        except IndexError:
            raise MWTDataError("Could not find summary file in target path.")

        self.basename = os.path.splitext(os.path.basename(self.summary))[0]

    def _find_blobs_files(self):
        """
        Find blobs files and verify consecutiveness
        """
        self.blobs_files = sorted(glob.glob(os.path.join(
                self.data_path, self.basename + '_?????k.blobs')))
        for i, fn in enumerate(self.blobs_files):
            expected_fn = '{}_{:05}k.blobs'.format(self.basename, i)
            if not fn.endswith(expected_fn):
                raise MWTDataError("Experiment data missing a consecutive "
                        "blobs file. ({})".format(expected_fn))

    def _find_images(self):
        """
        Find related images and store them indexed by seconds (and fractions 
        thereof)
        """
        self.image_files = {}
        image_re_mask = re.compile(re.escape(self.basename) 
                + r'(?P<frame>[0-9]*)\.png$')
        for image in glob.glob(os.path.join(self.data_path, self.basename + '*.png')):
            match = image_re_mask.search(image)
            frame_num = match.group('frame')
            self.image_files[int('0' + frame_num) / 1000] = image

    def add_summary_filter(self, f):
        """
        Add a function `f` that can be passed a blobs_summary Numpy structured 
        array and removes undesirable rows.
        """
        self.summary_filters.append(f)

    def add_filter(self, f):
        """
        Add a function `f` that can be passed a fully parsed blobs_data item 
        and returns whether or not it should be kept.
        """
        # The item (key/value pair) is passed, but the filter should only
        # bother with the value.
        self.filters.append(lambda item: f(item[1]))

    def load_summary(self):
        """
        Loads the location of blobs in the \*.blobs data files.

        Must be called prior to attempting to access any blob with 
        :func:`good_blobs`, :func:`parse_blob`, or the like.
        """
        bs, self.frame_times = summary.parse(self.summary)
        if bs['file_no'].max() + 1 > len(self.blobs_files):
            raise MWTDataError("Summary file refers to missing blobs files.")

        # filter and create blob id mapping 
        self.blobs_summary = multifilter_block(self.summary_filters, bs)
        self.bs_mapping = summary.make_mapping(self.blobs_summary)

        # the maximum number of blobs we'll ever need to deal with
        self.max_blobs = len(self.blobs_summary)

    def _blob_lines(self, bid):
        """
        Generator that yields all lines of data for blob id `bid`.
        """
        file_no, offset = self.blobs_summary[['file_no', 'offset']][self.bs_mapping[bid]]
        with open(self.blobs_files[file_no], 'r') as f:
            f.seek(offset)
            if six.next(f).rstrip() != '% {}'.format(bid):
                raise MWTDataError("File number/offset for blob {} was "
                        "incorrect.".format(bid))
            for line in f:
                if line[0] != '%':
                    yield line
                else:
                    return

    def parse_blob(self, bid, parser=None):
        """
        Parses the specified blob `parser` that 
        accepts a generator returning all raw data lines from the blob.

        Parameters
        ----------
        bid : int
            The blob ID to parse.

        parser : callable, optional
            A function that accepts one positional argument, a generator 
            that yields all data lines from blob `bid`.  The default parser
            is :func:`.blob.parse`.

        Returns
        -------
        object
            The output from `parser`.
        """
        if parser is None:
            parser = blob.parse
        return parser(self._blob_lines(bid))

    def all_blobs(self, parser=None):
        """
        Generator that parses and yields all the blobs in the summary data 
        using :func:`parse_blob`.
        """
        for bid in self.blobs_summary['bid']:
            yield bid, self.parse_blob(bid, parser=parser)
            self.blobs_parsed += 1

    def good_blobs(self, parser=None):
        """
        Generator that produces filtered blobs.  You could route the output 
        to a database, memory, or whereever.  See :func:`parse_blob` for how 
        the blobs are parsed.
        """
        for blob in multifilter(self.filters, self.all_blobs(parser=parser)):
            yield blob
            blob = None # free mem

    # def load_blobs(self):
    #     """
    #     Loads all blobs into memory.  Probably will crash for a typical 
    #     experiment if not a 64-bit OS with a healthy amount of RAM.
    #     """
    #     for bid, blob in self.good_blobs():
    #         self.blobs_data[bid] = blob

    def progress(self):
        return self.blobs_parsed, self.max_blobs
