#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generates a scoring function from worm data that can be fed a time and 
distance gap to predict connected worm tracks.
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

class DisplacementScorer(object):
    def __init__(self, displacements):
        self.kdes = [None] # ...something
        for column in displacements:
            pass
            # make a KDE for each slice of data

    def __call__(self, dgap, fgap):
        return
