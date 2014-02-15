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

from ..util import multifilter, alternate
from . import blob

# BlobSummary = collections.namedtuple('BlobSummary', [
#         'location',
#         'from_id',
#         'to_id',
#         'lifetime',
#         'lifetime_f',
#     ])
# BlobData = collections.namedtuple('BlobData', [
#         '',
#     ])

class MWTDataError(Exception):
    """
    Generic Error class for something wrong with the MWT output data
    """
    pass

def parse_line_segment(line_segment):
    # line segments ususally contain an unspecified number of paired values.
    # this parses the paired values and returns them as two lists, part_a and part_b        
    elements = line_segment.split()
    if len(elements) % 2:
        raise ValueError('Odd number of elements when split.')

    return alternate(elements)


class Experiment(object):
    """
    Provides interfaces for Multi-Worm Tracker experiment data.  Initalized 
    with a path to the experiment data, it identifies the related files and 
    gives methods to load data into memory and/or parse selected blobs.

    General workflow:

    * Initalize object with path
    * Add desired filters
    * Load summary file
    * Store data by either:
      * Using provided generator to pull good blobs and storing somewhere 
        else (e.g. a database)
      * Call the loader function that pulls all blobs and stores them in 
        the local instance
    """
    def __init__(self, data_path):
        self.find_summary_file(data_path)
        self.find_blobs_files(data_path)
        self.find_images(data_path)

        # typical key/item example:
        # blob_id: {
        #    'location': (file_no, offset),
        #    'born': time_found, 
        #    'born_f': frame_found, 
        #    'died': time_lost, 
        #    'died_f': frame_lost, 
        # }
        self.blobs_summary = {}

        # typical key/item example:
        # blob_id: {
        #    'lifetime_f': life_in_frames, 
        #    ...
        # }
        #self.blobs_data = {}
        
        self.summary_filters = []
        self.filters = []

        # Upper bound of how many blobs there will be (for array
        # preallocation)
        self.max_blobs = None

        self.blobs_parsed = 0

    def find_summary_file(self, data_path):
        try:
            summaries = glob.glob(os.path.join(data_path, '*.summary'))
            if len(summaries) > 1:
                raise MWTDataError("Multiple summary files in target path.")
            self.summary = summaries[0]
        except IndexError:
            raise MWTDataError("Could not find summary file in target path.")

        self.basename = os.path.splitext(os.path.basename(self.summary))[0]

    def find_blobs_files(self, data_path):
        """
        Find blobs files and verify consecutiveness
        """
        self.blobs_files = sorted(glob.glob(os.path.join(
                data_path, self.basename + '*.blobs')))
        for i, fn in enumerate(self.blobs_files):
            expected_fn = '{}_{:05}k.blobs'.format(self.basename, i)
            if not fn.endswith(expected_fn):
                raise MWTDataError("Experiment data missing a consecutive "
                        "blobs file. ({})".format(expected_fn))

    def find_images(self, data_path):
        """
        Find related images and store them indexed by seconds (and fractions 
        thereof)
        """
        self.image_files = {}
        image_re_mask = re.compile(re.escape(self.basename) 
                + r'(?P<frame>[0-9]*)\.png$')
        for image in glob.glob(os.path.join(data_path, self.basename + '*.png')):
            match = image_re_mask.search(image)
            frame_num = match.group('frame')
            self.image_files[int('0' + frame_num) / 1000] = image


    def add_summary_filter(self, f):
        """
        Add a function that can be passed a blobs_summary item and returns 
        whether or not it should be kept.
        """
        # The item (key/value pair) is passed, but the filter should only
        # bother with the value.
        self.summary_filters.append(lambda item: f(item[1]))

    def add_filter(self, f):
        """
        Add a function that can be passed a fully parsed blobs_data item 
        and returns whether or not it should be kept.
        """
        # The item (key/value pair) is passed, but the filter should only
        # bother with the value.
        self.filters.append(lambda item: f(item[1]))

    def load_summary(self):
        blobs_summary = defaultdict(dict, {})
        # to verify there as many blobs files as the summary expects
        max_fnum = -1
        with open(self.summary, 'r') as f:
            active_blobs = set()
            for line in f:
                # store all blob locations and remove them from end of line.
                splitline = line.split('%%%')
                if len(splitline) == 2:
                    line, file_offsets = splitline
                    blobs, locations = parse_line_segment(file_offsets)
                    for b, l in zip(blobs, locations):
                        b = int(b)
                        fnum, offset = (int(x) for x in l.split('.'))
                        blobs_summary[b]['location'] = fnum, offset
                        max_fnum = max(max_fnum, fnum)

                # store all blob start and end times and remove them from end of line.
                splitline = line.split('%%')
                if len(splitline) == 2:
                    line, blob_connections = splitline
                    frame, time = line.split()[:2]
                    frame = int(frame)
                    time = float(time)

                    lost_bids, found_bids = alternate(
                            [int(i) for i in blob_connections.split()])
                    for b in found_bids:
                        blobs_summary[b]['born'] = time
                        blobs_summary[b]['born_f'] = frame
                        active_blobs.add(b)
                    for b in lost_bids:
                        blobs_summary[b]['died'] = time
                        blobs_summary[b]['died_f'] = frame
                        active_blobs.discard(b)

            # wrap up blob ends with the time
            for bid in active_blobs:
                blobs_summary[bid]['died'] = time
                blobs_summary[bid]['died_f'] = frame

        # delete dummy blob id
        del blobs_summary[0]

        self.blobs_summary = dict(
                multifilter(
                    [lambda it: 'location' in it[1]] + self.summary_filters, 
                    six.iteritems(blobs_summary)
                )
            )

        self.max_blobs = len(self.blobs_summary)

        if max_fnum + 1 > len(self.blobs_files):
            raise MWTDataError("Summary file refers to missing blobs files.")

        for v in self.blobs_summary.values():
            assert set(v.keys()) == set((
                    'born', 'born_f', 'died', 'died_f', 'location'))

    def _blob_lines(self, bid):
        """
        Generator that yields all lines of data for blob id *bid*.
        """
        fnum, offset = self.blobs_summary[bid]['location']
        with open(self.blobs_files[fnum], 'r') as f:
            f.seek(offset)
            assert six.next(f).rstrip() == '% {}'.format(bid)
            for line in f:
                if not line.startswith('%'):
                    yield line

    def parse_blob(self, bid):
        """
        Parses the blob with id *bid*.
        """
        return blob.parse(self._blob_lines(bid))

    def all_blobs(self):
        """
        Generator that parses and yields all the blobs in the summary data.
        """
        for bid in self.blobs_summary:
            blob_info, blob_geometry = self.parse_blob(bid)
            blob_info.update(blob_geometry)
            blob_geometry = None # free mem

            self.blobs_parsed += 1
            yield bid, blob_info
            bid, blob_info = None, None # free mem

    def good_blobs(self):
        """
        Generator that produces filtered blobs.  Use to pipe the data to 
        another target.
        """
        for blob in multifilter(self.filters, self.all_blobs()):
            yield blob
            blob = None # free mem

    def load_blobs(self):
        """
        Loads all blobs into memory.  Probably will crash for a typical 
        experiment if not a 64-bit OS with a healthy amount of RAM.
        """
        for bid, blob in self.good_blobs():
            self.blobs_data[bid] = blob

    def progress(self):
        return self.blobs_parsed, self.max_blobs
