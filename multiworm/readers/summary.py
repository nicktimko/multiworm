#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MWT summary file manipulations
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import pathlib
from collections import defaultdict

import numpy as np
import networkx as nx

from ..core import MWTSummaryError
from ..util import alternate, dtype

SUMMARY_FIELDS = dtype([
        ('bid', 'int32'),
        ('file_no', 'int16'),
        ('offset', 'int32'),
        ('born', 'float64'),
        ('born_f', 'int32'),
        ('died', 'float64'),
        ('died_f', 'int32'),
    ])

def find(directory):
    try:
        summaries = list(directory.glob('*.summary'))
        if len(summaries) > 1:
            raise MWTSummaryError("Multiple summary files in specified directory; ambiguous")
        summary = summaries[0]
    except IndexError:
        raise MWTSummaryError("Could not find summary file in target path: {}"
                              .format(directory))

    basename = summary.stem

    return summary, basename

def parse(path, graph=False):
    """
    Parses the summary file at *path*, and returns a Numpy structured
    array containing the following columns:

        1. `bid`: ID
        2. `file_no`: \*.blob file number
        3. `offset`: Blob byte offset within file
        4. `born`: Time found
        5. `born_f`: Frame found
        6. `died`: Time lost
        7. `died_f`: Frame lost
    """
    blobs_summary = defaultdict(dict, {})
    section_delims = {'%': 'events', '%%': 'lost_and_found', '%%%': 'offsets'}
    active_blobs = set()
    frame_times = []
    if graph:
        digraph = nx.DiGraph()

    with path.open('r') as f:
        for line_num, line in enumerate(f, start=1):
            # store all blob locations and remove them from end of line.
            line = line.split()
            frame = int(line[0])
            time = float(line[1])

            if frame != line_num:
                raise MWTSummaryError("Error in summary file, line {} has "
                        "unexpected frame number ({}).".format(line_num, frame))

            frame_times.append(time)

            if len(line) == 15:
                # if there are only 15 fields (which would mean no %/%%/%%%
                # sections), nothing was lost/found on this frame so there
                # isn't anything left to do.
                continue
            elif len(line) < 15:
                raise MWTSummaryError("Malformed summary file, line {} has "
                        "an invalid number of fields (<15)".format(line_num))

            # split up the remaining data into whatever section
            data = {'events': [], 'lost_and_found': [], 'offsets': []}
            section = None
            for element in line[15:]:
                if element in section_delims:
                    section = section_delims[element]
                else:
                    data[section].append(element)

            for b, l in zip(*alternate(data['offsets'])):
                b = int(b)
                fnum, offset = (int(x) for x in l.split('.'))
                blobs_summary[b]['location'] = fnum, offset

            # store all blob start and end times and remove them from end of line.
            lost_bids, found_bids = alternate([int(i) for i in data['lost_and_found']])

            if graph:
                for parent, child in zip(lost_bids, found_bids):
                    if parent == 0:
                        digraph.add_node(child)
                    elif child != 0:
                        digraph.add_edge(parent, child)

            for b in found_bids:
                blobs_summary[b]['born'] = time
                blobs_summary[b]['born_f'] = frame
                if graph and b != 0:
                    digraph.node[b]['born'] = frame
                active_blobs.add(b)
            for b in lost_bids:
                blobs_summary[b]['died'] = time
                blobs_summary[b]['died_f'] = frame - 1
                if graph and b != 0:
                    digraph.node[b]['died'] = frame
                active_blobs.discard(b)

        # wrap up blob ends with the time
        for bid in active_blobs:
            blobs_summary[bid]['died'] = time
            blobs_summary[bid]['died_f'] = frame
            if graph and bid != 0:
                digraph.node[bid]['died'] = frame

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

    if graph:
        return blobs_summary_recarray, frame_times, digraph
    else:
        return blobs_summary_recarray, frame_times

def make_mapping(summary_data):
    """
    Create a mapping from blob IDs to the record number
    """
    return dict(zip(summary_data['bid'], range(len(summary_data))))
