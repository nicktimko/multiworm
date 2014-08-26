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
import warnings

from .core import MWTDataError
from .readers import blob, summary, image
from .util import multifilter, multitransform
from .filters import exists_in_frame
from .blob import Blob

class Experiment(object):
    """
    Provides interfaces for Multi-Worm Tracker experiment data.

    Provide the *experiment_id* string (folder name) for the experiment
    contained within *data_root*.  If *data_root* is not specified, it is
    the current working directory.

    Next, pass filter functions to :func:`add_summary_filter` and/or
    :func:`add_filter`.  Then call :func:`load_summary` to index the location
    of all possible good blobs.
    """
    def __init__(self, fullpath=None, experiment_id=None, data_root=''):
        if fullpath:
            self.directory = pathlib.Path(fullpath)
            self.id = self.directory.stem
        else:
            if experiment_id is None:
                raise ValueError('experiment_id must be provided if the full '
                    'path to the experiment data is not.')
            self.directory = pathlib.Path(data_root) / experiment_id
            self.id = experiment_id

        self._find_summary_file()
        self._find_blobs_files()
        self._find_images()

        self.summary = None

        self.blobs_parsed = 0
        self._load_summary()

    def __iter__(self):
        return iter(self.summary.index)

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
        self.image_files = image.ImageFileOrganizer(
                image.find(self.directory, self.basename),
                experiment=self)

    def load_summary(self, graph=None):
        notice = ('load_summary() does nothing, summary file is '
                  'automatically loaded on object initialization')
        warnings.warn(notice, Warning)

    def _load_summary(self):
        """
        Loads the location of blobs in the \*.blobs data files.

        Must be called prior to attempting to access any blob with
        :func:`good_blobs`, :func:`parse_blob`, or the like.
        """
        self.summary, self.frame_times, self.graph = summary.parse(self.summary_file)

        # check size is non-zero to not error out on empty data sets
        if not self.summary.empty:
            file_refs = int(self.summary['file_no'].max()) + 1
            file_count = len(self.blobs_files)
            if file_refs > file_count:
                raise MWTDataError("Summary refers to missing blobs files "
                        "({} out of {} found).".format(file_count, file_refs))

    def blobs_in_frame(self, frame):
        return exists_in_frame(frame)(self.summary).index

    def summary_data(self, bid):
        """
        Returns summary data on blob *bid*
        """
        return self.summary.loc[bid]

    def _blob_lines(self, bid):
        """
        Generator that yields all lines of data for blob id `bid`.
        """
        file_no, offset = self.summary[['file_no', 'offset']].loc[bid].astype(int)
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

    def parse_blob(self, *args, **kwargs):
        notice = ('parse_blob is now internal, index the experiment to '
                  'get a Blob object')
        warnings.warn(notice, Warning)

        return self._parse_blob(*args, **kwargs)

    def _parse_blob(self, bid, parser=None):
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
