#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core functions and objects
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

class OneGoodBlobException(Exception):
    """
    For when there's only one good blob.  Causes some errors if not handled 
    deliberately.
    """
    pass
