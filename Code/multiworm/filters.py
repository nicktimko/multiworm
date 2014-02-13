#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Filters to provide an Experiment instance to pare down the amount of data
to look at.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from future.builtins import *

def minimum_time(threshold):
    """
    Returns a function used to filter blob data by a minimum time, 
    *threshold*.  Works either as a summary filter or general filter, but 
    much more efficient to use in the summary phase.
    """
    def f(blob):
        return blob['died'] - blob['born'] >= threshold
    return f
