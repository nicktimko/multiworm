# -*- coding: utf-8 -*-
"""
multiworm default configuration
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os
import pathlib

# /home/projects/worm_movement/Data/MWT_RawData is a good idea for 
# workstations, but this may fail/crash on Windows.  Force user to specify.
MWT_DATA_ROOT = pathlib.Path()
