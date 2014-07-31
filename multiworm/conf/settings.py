# -*- coding: utf-8 -*-
"""
Multiworm configuration management.  Inspired by Django's settings module.  To
override defaults, specify the module you want to superscede by setting (or
setdefault) the MULTIWORM_SETTINGS environment variable.  The value of the
envvar must be importable.

    os.environ.setdefault('MULTIWORM_SETTINGS', 'my_config')
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os
import importlib #2.7+
import warnings

from . import defaults

REQUIRE_SETTINGS_MODULE = False

ENVIRONMENT_VARIABLE = 'MULTIWORM_SETTINGS'

class Settings(object):
    def __init__(self, local_module_name):
        # copy attributes from the default settings
        for field in dir(defaults):
            if field.isupper():
                setattr(self, field, getattr(defaults, field))

        self.LOCAL_MODULE = local_module_name

        if REQUIRE_SETTINGS_MODULE:
            if local_module_name is None:
                raise EnvironmentError("{} environmental variable "
                    "not specified.  Set the variable before importing multiworm "
                    "to configure local settings."
                    .format(ENVIRONMENT_VARIABLE))

        if local_module_name:
            # attempt to import
            try:
                local_module = importlib.import_module(local_module_name)
            except ImportError:
                raise ImportError("Failed to load settings module: {}"
                                  .format(local_module_name))

            # overwrite attributes loaded from default with local settings
            rogue_fields = []
            for field in dir(local_module):
                if field.isupper():
                    if not hasattr(self, field):
                        # see below
                        rogue_fields.append(field)
                    setattr(self, field, getattr(local_module, field))

            # notify users if there is an unexpected setting. could be either a
            # typo, or a "local-only" setting which may result in code that works
            # locally, but will crash when internal code attempts to reference a
            # non-existent attribute (gonna have a bad time).
            if rogue_fields:
                warnings.warn("Local settings included field(s): {} which have no "
                        "defaults.  Possible typo?"
                        .format(', '.join("'{}'".format(f) for f in rogue_fields)))

local_settings = os.environ.get(ENVIRONMENT_VARIABLE)
settings = Settings(local_settings)