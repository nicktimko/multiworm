#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core functions and objects
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

class MWTDataError(Exception):
    """
    Generic error to signal a problem with the MWT output data files.
    """
    pass


class MWTSummaryError(MWTDataError):
    """
    An error having to do with the summary file
    """


class MWTBlobsError(MWTDataError):
    """
    An error having to do with the blobs file(s)
    """

