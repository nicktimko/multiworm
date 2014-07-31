# -*- coding: utf-8 -*-
"""
Multiworm configuration management.  Inspired by Django's settings module.  To
override defaults, specify the module you want to superscede by setting (or
setdefault) the MULTIWORM_SETTINGS environment variable.

    os.environ.setdefault('MULTIWORM_SETTINGS', 'my_config')
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os
import importlib

from . import defaults
from .settings import settings
