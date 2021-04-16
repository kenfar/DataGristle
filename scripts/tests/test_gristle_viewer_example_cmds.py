#zR!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2020-2021 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

from pprint  import pprint as pp
import os
from os.path import dirname, basename, join as pjoin
import sys
import tempfile


import datagristle.csvhelper as csvhelper
import datagristle.test_tools as test_tools

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_viewer')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))




class TestExamples(test_tools.TestExamples):
    """ Test all configs and files in the example directory for this program
    """
    def setup_method(self, method):
        super().setup_method(method)

        self.pgm = 'gristle_viewer'
        self.example_dir = EXAMPLE_DIR
        self.script_dir = SCRIPT_DIR
        self.temp_dir = tempfile.mkdtemp(prefix=self.pgm)
