#!/usr/bin/env python
import sys

if not sys.hexversion >= 0x02070000:
    raise RuntimeError("Python 2.7 or newer is required")

from setuptools import setup

setup(name='multiworm',
    version='0.0.1',
    description='Python interface for Multi-Worm Tracker data',
    author='Nick Timkovich',
    author_email='npt@u.northwestern.edu',
    url='https://bitbucket.org/nick_timkovich/multiworm',
    packages=['multiworm'],
    #scripts=['arpeggio'],
    classifiers=[
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Intended Audience :: Science/Research',
    ],
    install_requires=[
        'future==0.11.2'
        #'numpy>=1.6.1',
        #'scipy>=0.11.0',
        #'matplotlib>=1.2.1',

    ],
    # test_requires=[
    #     'nose>=1.3.0',
    # ],
    )
