#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handles data from a Multi-Worm Tracker experiment
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import pathlib

from .core import MWTDataError
from .conf import settings
from .readers import blob, summary, image
from .util import multifilter, multitransform
from .filters import exists_in_frame
from .blob import Blob

class Experiment(object):
    """
    Provides interfaces for Multi-Worm Tracker experiment data.

    Provide the *experiment_id* string (folder name) for the experiment
    contained within *data_root*.  If *data_root* is not specified, it is
    pulled from the settings file loaded from trying to import the environment
    variable ``MULTIWORM_SETTINGS``.

    Next, pass filter functions to :func:`add_summary_filter` and/or
    :func:`add_filter`.  Then call :func:`load_summary` to index the location
    of all possible good blobs.
    """
    def __init__(self, fullpath=None, experiment_id=None, data_root=None):
        if fullpath:
            self.directory = pathlib.Path(fullpath)
            self.experiment_id = directory.stem
        else:
            if experiment_id is None:
                raise ValueError('experiment_id must be provided if the full '
                    'path to the experiment data is not.')
            if data_root is None:
                data_root = settings.MWT_DATA_ROOT
            self.directory = pathlib.Path(data_root) / experiment_id
            self.experiment_id = experiment_id

        self._find_summary_file()
        self._find_blobs_files()
        self._find_images()

        #self.metadata = MetadataManager(self.directory, self.basename)

        self.summary = None

        self.summary_filters = []
        self.filters = []

        # Upper bound of how many blobs there will be (for array
        # preallocation)
        self.max_blobs = None

        self.blobs_parsed = 0

    def __iter__(self):
        return iter(self.summary['bid'])

    def blobs(self):
        for blob_id in self:
            yield blob_id, self[blob_id]

    def __getitem__(self, key):
        return Blob(self, key)

    def _find_summary_file(self):
        """
        Locate summary file
        """
        self.summary_file, self.basename = summary.find(self.directory)

    def _find_blobs_files(self):
        """
        Locate blobs files
        """
        self.blobs_files = blob.find(self.directory, self.basename)

    def _find_images(self):
        """
        Locate images
        """
        self.image_files = image.find(self.directory, self.basename)

    def add_summary_filter(self, f):
        """
        Add a function `f` that can be passed a summary Numpy structured
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

    def load_summary(self, graph=False):
        """
        Loads the location of blobs in the \*.blobs data files.

        Must be called prior to attempting to access any blob with
        :func:`good_blobs`, :func:`parse_blob`, or the like.
        """
        if graph:
            bs, self.frame_times, self.collision_graph = summary.parse(
                    self.summary_file, graph=True)
        else:
            bs, self.frame_times = summary.parse(self.summary_file)
        # check size is non-zero to not error out on empty data sets
        if bs.size:
            file_refs = bs['file_no'].max() + 1
            file_count = len(self.blobs_files)
            if file_refs > file_count:
                raise MWTDataError("Summary refers to missing blobs files "
                        "({} out of {} found).".format(file_count, file_refs))

        # filter and create blob id mapping
        self.summary = multitransform(self.summary_filters, bs)
        self.bs_mapping = summary.make_mapping(self.summary)

        # the maximum number of blobs we'll ever need to deal with
        self.max_blobs = len(self.summary)

    def blobs_in_frame(self, frame):
        return exists_in_frame(frame)(self.summary)['bid']

    def summary_data(self, bid):
        """
        Returns summary data on blob *bid*
        """
        return self.summary[self.bs_mapping[bid]]

    def _blob_lines(self, bid):
        """
        Generator that yields all lines of data for blob id `bid`.
        """
        file_no, offset = self.summary[['file_no', 'offset']][self.bs_mapping[bid]]
        with self.blobs_files[file_no].open('r') as f:
            f.seek(offset)
            if six.next(f).rstrip() != '% {0}'.format(bid):
                raise MWTDataError("File number/offset ({}/{}) for blob {} "
                        "was incorrect.".format(file_no, offset, bid))
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

        Keyword Arguments
        -----------------
        parser : callable
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
        for bid in self.summary['bid']:
            yield bid, self.parse_blob(bid, parser=parser)
            self.blobs_parsed += 1

    def good_blobs(self, parser=None):
        """
        Generator that produces filtered blobs.  You could route the output
        to a database, memory, or whereever.  See :func:`parse_blob` for how
        the blobs are parsed.  Note that the filters provided in
        :func:`add_filter` (if any) must be compatible with (accept) what
        the parser returns.
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
        """
        A crude indicator of progress as blobs are processed.

        Returns the number of blobs parsed (including those filtered out) out
        of the total number of blobs that will be.  If called after every
        output from :func:`good_blobs`, and there are any filters that have
        an effect, the first number will skip.
        """
        return self.blobs_parsed, self.max_blobs
