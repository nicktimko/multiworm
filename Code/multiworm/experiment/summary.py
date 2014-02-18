#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MWT summary file manipulations
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

from collections import defaultdict

import numpy as np

from ..util import alternate, dtype

# def parse_line_segment(line_segment):
#     # line segments ususally contain an unspecified number of paired values.
#     # this parses the paired values and returns them as two lists, part_a and part_b        
#     elements = line_segment.split()
#     if len(elements) % 2:
#         raise ValueError('Odd number of elements when split.')

#     return alternate(elements)

SUMMARY_FIELDS = dtype([
        ('bid', 'int32'),
        ('file_no', 'int16'),
        ('offset', 'int32'),
        ('born', 'float64'),
        ('born_f', 'int32'),
        ('died', 'float64'),
        ('died_f', 'int32'),
    ])

def parse(file_path):
    """
    Parses the summary file at *filepath*, and returns a Numpy structured 
    array containing the following columns:

        1. ID ('bid')
        2. *.blob file number ('file_no')
        3. Blob byte offset within file ('offset')
        4. Time found ('born')
        5. Frame found ('born_f')
        6. Time lost ('died')
        7. Frame lost ('died_f')
    """
    blobs_summary = defaultdict(dict, {})
    with open(file_path, 'r') as f:
        active_blobs = set()
        for line in f:
            # store all blob locations and remove them from end of line.
            splitline = line.split('%%%')
            if len(splitline) == 2:
                line, file_offsets = splitline
                blobs, locations = alternate(file_offsets.split())
                for b, l in zip(blobs, locations):
                    b = int(b)
                    fnum, offset = (int(x) for x in l.split('.'))
                    blobs_summary[b]['location'] = fnum, offset

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

    blobs_summary = dict(filter(
            lambda it: 'location' in it[1], six.iteritems(blobs_summary)
        ))

    # convert to Numpy Structured Array
    blobs_summary_recarray = np.zeros((len(blobs_summary),), dtype=SUMMARY_FIELDS)
    for i, blob in enumerate(six.iteritems(blobs_summary)):
        bid, bdata = blob
        blobs_summary_recarray[i] = (bid, 
                bdata['location'][0], bdata['location'][1],
                bdata['born'], bdata['born_f'], 
                bdata['died'], bdata['died_f'])

    return blobs_summary_recarray

def make_mapping(summary_data):
    """
    Create a mapping from blob IDs to the record number
    """
    return dict(zip(summary_data['bid'], range(len(summary_data))))