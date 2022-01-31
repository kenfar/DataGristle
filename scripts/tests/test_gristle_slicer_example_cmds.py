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

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_slicer')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestExamples(test_tools.TestExamples):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        super().setup_method(method)

        self.pgm = 'gristle_slicer'
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


    def test_example_21_indiv_rows_and_cols(self):
        self.run_example_config('example-21')

    def test_example_22_ranges(self):
        self.run_example_config('example-22')

    def test_example_23_exclusions(self):
        self.run_example_config('example-23')

    def test_example_24_inclusions_and_exclusions(self):
        self.run_example_config('example-24')

    def test_example_25_field_names(self):
        self.run_example_config('example-25')

    def test_example_26_out_of_order(self):
        self.run_example_config('example-26')

    def test_example_27_slice_stepping(self):
        self.run_example_config('example-27')

    def test_example_28_reverse_slice_stepping(self):
        self.run_example_config('example-28')

    # It's random, to test this we'll need to add a ton more rows, and then look for a count of
    # the output that's close to 25%
    #
    #def test_example_29_random_slice_stepping(self):
    #    self.run_example_config_for_return_code('example-29')

    def test_example_30_repeated_rows_and_cols(self):
        self.run_example_config('example-30')

    def test_example_31_unbounded_ranges(self):
        self.run_example_config('example-31')
