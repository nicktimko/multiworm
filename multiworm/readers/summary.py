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
import pandas as pd
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

def parse(path):
    """
    Parses the summary file at *path*, and returns:

      1. a pandas.DataFrame with the following columns:
        * `bid`: ID
        * `file_no`: \*.blob file number
        * `offset`: Blob byte offset within file
        * `born_t`: Time found
        * `born_f`: Frame found
        * `died_t`: Time lost
        * `died_f`: Frame lost

      2. a list of "wall-clock" times corresponding to frame times

      3. a networkx.DiGraph of fission and fusion events
    """
    dd = defaultdict(dict, {}) # 'data dict', later turned into a dataframe
    section_delims = {'%': 'events', '%%': 'lost_and_found', '%%%': 'offsets'}
    active_blobs = set()
    frame_times = []
    digraph = nx.DiGraph()

    with path.open('r') as f:
        prev_time = 0
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
                (dd[b]['file_no'],
                 dd[b]['offset']) = (int(x) for x in l.split('.'))

            # store all blob start and end times and remove them from end of line.
            lost_bids, found_bids = alternate([int(i) for i in data['lost_and_found']])

            for parent, child in zip(lost_bids, found_bids):
                if parent == 0:
                    digraph.add_node(child)
                elif child != 0:
                    digraph.add_edge(parent, child)

            for b in found_bids:
                dd[b]['born_t'] = time
                dd[b]['born_f'] = frame
                if b != 0:
                    digraph.node[b]['born_f'] = frame
                active_blobs.add(b)

            for b in lost_bids:
                dd[b]['died_t'] = prev_time
                dd[b]['died_f'] = frame - 1
                if b != 0:
                    digraph.node[b]['died_f'] = frame - 1
                active_blobs.discard(b)

            prev_time = time

        # wrap up blob ends with the time
        for bid in active_blobs:
            dd[bid]['died_t'] = time
            dd[bid]['died_f'] = frame
            if bid != 0:
                digraph.node[bid]['died_f'] = frame

    del dd[0] # drop fake blob

    df = pd.DataFrame.from_dict(dd, orient='index')

    # MWT bug fixing: sometimes blobs near the start don't actually have a
    # start time.  We're just going to drop them from analysis (they have
    # not been emperically shown to have any data associated with them).
    born_nan = df[~np.isfinite(df['born_f'])].index
    died_nan = df[~np.isfinite(df['died_f'])].index
    for term_nan in [born_nan, died_nan]:
        if len(term_nan) != 0:
            df.drop(df.index[term_nan])
            digraph.remove_nodes_from(term_nan)

    # pretty it up (for debugging, pointless otherwise)
    #df = df[['born_t', 'died_t', 'born_f', 'died_f', 'file_no', 'offset']]

    # local graph should be immutable
    digraph = nx.freeze(digraph)

    def unlock():
        return nx.DiGraph(digraph)
    digraph.copy = unlock

    return df, frame_times, digraph
