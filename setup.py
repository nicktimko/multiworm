#!/usr/bin/env python
import sys
import setuptools

if not sys.hexversion >= 0x02060000:
    raise RuntimeError("Python 2.6 or newer is required")

from setuptools import setup

setup(
    name='multiworm',
    version='0.1.0',
    description='Python interface for Multi-Worm Tracker data',
    packages=['multiworm'],

    author='Nick Timkovich',
    author_email='npt@u.northwestern.edu',
    url='https://github.org/nicktimko/multiworm',

    long_description=open('README.rst', 'r').read(),
    keywords=[
        'c. elegans', 'caenorhabditis elegans', 'caenorhabditis', 'elegans',
        'worm', 'tracking', 'biology', 'amaral',
    ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],

    install_requires=[
        'networkx>=1.8.1',
        'numpy>=1.8.1',
        'pandas>=0.14.0',
        'pathlib>=1.0.1',
        # 'scipy>=0.11.0',
        'six>=1.7.2',
    ],

    test_requires=[
        'nose>=1.3.0',
        'scipy>=0.11.0',
    ],
)
