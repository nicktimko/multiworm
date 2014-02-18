#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Filters to provide an Experiment instance to pare down the amount of data
to look at.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import math

def summary_lifetime_minimum(threshold):
    """
    Returns a function that filters summary blob data by a minimum time, 
    *threshold*.
    """
    def f(summary_data):
        lifetimes = summary_data['died'] - summary_data['born']
        return summary_data[lifetimes >= threshold]
    return f

def _midline_length(points):
    """
    Calculates the length of a path connecting *points*.
    """
    dist = 0
    ipoints = iter(points)
    a = six.next(ipoints) # prime loop
    for b in ipoints:
        dist += math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        a = b
    return dist

def relative_move_minimum(threshold):
    """
    Returns a function that filters parsed blob data by a minimum amount 
    of movement.  The sum of the blob's centroid bounding box must exceed 
    *threshold* times the average length of the midline.
    """
    def f(blob):
        xcent, ycent = tuple(zip(*blob['centroid']))
        move_px = (max(xcent) - min(xcent)) + (max(ycent) - min(ycent))
        size_px = (
            sum(_midline_length(p) for p in blob['midline'] if p)
            / len(blob['midline']))
        return move_px >= size_px * threshold

    return f
