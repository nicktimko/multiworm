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

from ..core import MWTSummaryError, MWTDataError
from ..util import alternate, dtype

NO_DATA = -1 # something that could never exist

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

CALLBACK_DF_CHEAT = 0.8

def parse(path, callback=None):
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

    *callback* returns last **time** processed.
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
                    if frame == 1 and parent != 0: # no parents should be saved on first frame.
                        digraph.add_node(child)
                    else:
                        digraph.add_edge(parent, child)

            for b in found_bids:
                dd[b]['born_t'] = time
                dd[b]['born_f'] = frame
                if b != 0:
                    digraph.node[b]['born_t'] = time
                    digraph.node[b]['born_f'] = frame
                active_blobs.add(b)

            for b in lost_bids:
                if frame == 1:
                    continue # no blobs lost on the first frame have any record.

                dd[b]['died_t'] = prev_time
                dd[b]['died_f'] = frame - 1

                if b != 0:
                    digraph.node[b]['died_t'] = prev_time
                    digraph.node[b]['died_f'] = frame - 1
                active_blobs.discard(b)

            prev_time = time

            if callback:
                callback(time * CALLBACK_DF_CHEAT) # cheat this; making DF takes a while...

        # wrap up blob ends with the time
        for bid in active_blobs:
            dd[bid]['died_t'] = time
            dd[bid]['died_f'] = frame
            if bid != 0:
                digraph.node[bid]['died_t'] = time
                digraph.node[bid]['died_f'] = frame

    if len(dd) == 0:
        raise MWTDataError('No blobs in experiment.')

    del dd[0] # drop fake blob

    df = pd.DataFrame.from_dict(dd, orient='index')

    if not 'offset' in df.columns:
        # this hits if none of the dicts in dd had 'offset'/'file_no' keys
        # because there is no associated blobs data (for anything)
        raise MWTDataError('No blobs in experiment with data.')

    if callback:
        callback(time) # "complete"

    # MWT bug fixing: sometimes blobs near the start don't actually have a
    # start time.  We're just going to drop them from analysis (they have
    # not been emperically shown to have any data associated with them).
    born_nan = df[~np.isfinite(df['born_f'])].index
    died_nan = df[~np.isfinite(df['died_f'])].index
    for term_nan in [born_nan, died_nan]:
        if len(term_nan) != 0:
            df.drop(df.index[term_nan])
            digraph.remove_nodes_from(term_nan)

    # int-ify columns to avoid inadvertently passing floats as indicies
    # ** can't convert NaNs to int, fill with a sentinel (only will happen
    #    to the fn/offset columns, the empty born/died rows were removed
    #    above)
    int_cols = ['file_no', 'offset', 'born_f', 'died_f']
    df[int_cols] = df[int_cols].fillna(NO_DATA).astype(int)

    # pretty it up (for debugging, pointless otherwise)
    #df = df[['born_t', 'died_t', 'born_f', 'died_f', 'file_no', 'offset']]

    # local graph should be immutable
    digraph = nx.freeze(digraph)

    def unlock():
        return nx.DiGraph(digraph)
    digraph.copy = unlock

    return df, frame_times, digraph

FILL_VALUE = -1

class fields(object):
    born_f = 1
    died_f = 2
    born_t = 3
    died_t = 4
    file_no = 5
    offset = 6
    names = ['born_f', 'died_f', 'born_t', 'died_t', 'file_no', 'offset']

def init_array(n_columns, rows=100, dtype=np.int32):
    a = FILL_VALUE * np.ones((rows, n_columns + 1), dtype=dtype)
    a[...,0] = np.arange(rows)
    return a

def grow(arr, factor=4, expand_limit=100000):
    rows, cols = arr.shape
    new_rows = min(rows * factor, rows + expand_limit)
    expanded = FILL_VALUE * np.ones((new_rows, cols), dtype=arr.dtype)
    expanded[...,0] = np.arange(new_rows)
    expanded[:rows,...] = arr
    return expanded

def crush(arr):
    something = np.sum(arr[...,1:], axis=1) != (arr.shape[1] - 1) * FILL_VALUE

    # MWT bug fixing: sometimes blobs near the start don't actually have a
    # start time.  We're just going to drop them from analysis (they have
    # not been emperically shown to have any data associated with them).
    has_born = arr[...,fields.born_f] != FILL_VALUE
    has_died = arr[...,fields.died_f] != FILL_VALUE
    dropped_nodes = set(arr[something & (~has_born | ~has_died),0])

    return arr[something & has_born & has_died], dropped_nodes

def parse_np(path, callback=None):
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

    *callback* returns last **time** processed.
    """
    #aaa = ArrayAutoAllocator(n_columns=len(fields.names), dtype=np.int32)
    aaa = init_array(len(fields.names))

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
            time_ms = int(time * 1000 + 0.1)

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
            blob_events = {'events': [], 'lost_and_found': [], 'offsets': []}
            section = None
            for element in line[15:]:
                if element in section_delims:
                    section = section_delims[element]
                else:
                    blob_events[section].append(element)

            for b, l in zip(*alternate(blob_events['offsets'])):
                b = int(b)
                #dfp[b, ('file_no', 'offset')] = [int(x) for x in l.split('.')]
                aaa[b, fields.file_no], aaa[b, fields.offset] = (int(x) for x in l.split('.'))

            # store all blob start and end times and remove them from end of line.
            lost_bids, found_bids = alternate([int(i) for i in blob_events['lost_and_found']])

            for parent, child in zip(lost_bids, found_bids):
                if parent == 0:
                    digraph.add_node(child)
                elif child != 0:
                    if frame == 1 and parent != 0: # no parents should be saved on first frame.
                        digraph.add_node(child)
                    else:
                        digraph.add_edge(parent, child)

            for b in found_bids:
                if b > aaa[-1,0]:
                    aaa = grow(aaa)
                if b != 0:
                    aaa[b, fields.born_t] = time_ms
                    aaa[b, fields.born_f] = frame
                    digraph.node[b]['born_t'] = time
                    digraph.node[b]['born_f'] = frame
                active_blobs.add(b)

            for b in lost_bids:
                if frame == 1:
                    continue # no blobs lost on the first frame have any record.

                if b != 0:
                    aaa[b, fields.died_t] = prev_time_ms
                    aaa[b, fields.died_f] = frame - 1
                    digraph.node[b]['died_t'] = prev_time
                    digraph.node[b]['died_f'] = frame - 1
                active_blobs.discard(b)

            prev_time = time
            prev_time_ms = time_ms

            if callback and not (line_num % 100):
                callback(time * CALLBACK_DF_CHEAT) # cheat this; making DF takes a while...

        # wrap up blob ends with the time
        for bid in active_blobs:
            if bid != 0:
                aaa[bid, fields.died_t] = time_ms
                aaa[bid, fields.died_f] = frame
                digraph.node[bid]['died_t'] = time
                digraph.node[bid]['died_f'] = frame

    arr, dropped_nodes = crush(aaa)
    digraph.remove_nodes_from(dropped_nodes)

    df = pd.DataFrame(
            data=arr[...,1:], # slice off index col
            index=arr[...,0], # index col
            columns=fields.names,
        )

    if len(df) == 0:
        raise MWTDataError('No blobs in experiment.')

    if not np.any(df['offset'] != FILL_VALUE):
        # this hits if there is no associated blobs data (for anything)
        raise MWTDataError('No blobs in experiment with data.')

    if callback:
        callback(time) # "complete"

    # convert times back to seconds
    df['born_t'] = df['born_t'] / 1000
    df['died_t'] = df['died_t'] / 1000

    # local graph should be immutable
    digraph = nx.freeze(digraph)

    def unlock():
        return nx.DiGraph(digraph)
    digraph.copy = unlock

    return df, frame_times, digraph
