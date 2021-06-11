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
from os.path import dirname, join as pjoin
import tempfile


import datagristle.csvhelper as csvhelper
import datagristle.test_tools as test_tools

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_converter')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestExamples(test_tools.TestExamples):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        super().setup_method(method)

        self.pgm = 'gristle_converter'
        self.example_dir = EXAMPLE_DIR
        self.script_dir = SCRIPT_DIR
        self.temp_dir = tempfile.mkdtemp(prefix=self.pgm)

    def test_example_01(self):
        self.run_example_config('example-01')

    def test_example_02(self):
        self.run_example_config('example-02')

    def test_example_03(self):
        self.run_example_config('example-03')

    def test_example_04(self):
        self.run_example_config('example-04')

    def test_example_05(self):
        self.run_example_config('example-05')

    def test_example_06(self):
        self.run_example_config('example-06')

    def test_example_07(self):
        self.run_example_config('example-07')

    def test_example_21_quote_none_to_quote_all(self):
        self.run_example_config('example-21')
