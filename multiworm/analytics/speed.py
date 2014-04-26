# -*- coding: utf-8 -*-
"""
Assess the amount of noise present in an experiment
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

from .analytics import AnalysisMethod


class SpeedEstimator(AnalysisMethod):
    """
    Attempt to determine the amount of noise present in some worm recordings.
    """
    def __init__(self, **config):
        pass

    def process_blob(self, blob):
        pass
