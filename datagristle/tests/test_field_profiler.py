#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import tempfile
import csv
import os

from pprint import pprint as pp

import pytest

from datagristle import file_io
from datagristle import field_profiler as mod

INT_COL = 0
STRING_COL = 1
LOWER_COL = 2
UPPER_COL = 3
EMPTY_COL = 4
FLOAT_COL = 5
MIXED_COL = 6



class FileAndTestManager(object):
    """ Generic Test Class
    """

    def print_field(self, field_no):
        print('type:      %s' % self.MyFields.field_types[field_no])
        print('freq:     ')
        print(self.MyFields.field_freq[field_no])

    def customSettings(self):
        """ gets run from setup_method()
        """
        self.quoting = csv.QUOTE_NONE
        self.overrides = {}
        self.header = False

    def setup_method(self, method):

        self.customSettings()

        self.record_cnt = 100
        self.dialect = csv.Dialect
        self.dialect.quoting = csv.QUOTE_NONE
        self.dialect.quotechar = '"'
        self.dialect.has_header = self.header
        self.dialect.delimiter = ','
        self.dialect.skipinitialspace = False
        self.dialect.lineterminator = '\n'
        self.field_cnt = 7
        self.test1_fqfn = generate_test_file(self.dialect,
                                             self.record_cnt)
        # run FileTyper without csv dialect info:
        self.input_handler = file_io.InputHandler(files=[self.test1_fqfn], dialect=self.dialect)
        self.input_handler.get_field_count()
        self.input_handler.reset()

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)


    def test_deter_field_freq(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')

        #self.MyFields.analyze_fields(field_types_overrides=self.overrides)
        self.MyFields.analyze_fields()

        # there are 100 unique values for this column
        #assert len(self.MyFields.get_known_values(INT_COL)) == 11
        assert self.MyFields.field_profile[INT_COL].value_known_cnt == 11

        # there are 11 values for this column, show just 2
        assert len(self.MyFields.field_profile[INT_COL].get_top_values(limit=2)) == 2

        # there are only 2 values for these columns:
        assert len(self.MyFields.field_profile[INT_COL].get_top_values(limit=2)) == 2
        assert len(self.MyFields.field_profile[INT_COL].get_top_values(limit=2)) == 2

        # this is an empty field - it should show up as a single value with
        # occurance of 1
        assert len(self.MyFields.field_profile[EMPTY_COL].get_top_values(limit=2)) == 1

        # A is the most common value
        assert self.MyFields.field_profile[STRING_COL].get_top_values(limit=1)[0][0] == 'A'

        # check actual values coming back:
        assert self.MyFields.field_profile[FLOAT_COL].get_top_values(limit=1)[0][0] == '0.001'
        assert self.MyFields.field_profile[LOWER_COL].get_top_values(limit=1)[0][0] == 'bbb'


    def test_read_limit_truncation(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet',
                                           read_limit=5)

        self.MyFields.analyze_fields()

        # there are 100 unique values for this column normally, this time
        # it should be truncated at 5
        assert self.MyFields.field_profile[INT_COL].field_profiled_cnt == 5
        assert self.MyFields.field_profile[INT_COL].value_trunc is True
        assert self.MyFields.field_profile[STRING_COL].value_trunc is True
        assert self.MyFields.field_profile[EMPTY_COL].value_trunc is True
        assert self.MyFields.field_profile[FLOAT_COL].value_trunc is True
        assert self.MyFields.field_profile[MIXED_COL].value_trunc is True


    def test_maxfreq_truncation(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet',
                                           read_limit=5)
        self.MyFields.analyze_fields(max_value_counts=7)

        # there are 100 unique values for this column normally, this time
        # only high-cardinality cols should be truncated at 7
        assert self.MyFields.field_profile[INT_COL].value_known_cnt == 5
        assert self.MyFields.field_profile[INT_COL].value_trunc is True
        assert self.MyFields.field_profile[FLOAT_COL].value_known_cnt == 5
        assert self.MyFields.field_profile[FLOAT_COL].value_trunc is True
        # the rest of these have fewer values in their original data:
        assert self.MyFields.field_profile[EMPTY_COL].value_trunc is True
        assert self.MyFields.field_profile[MIXED_COL].value_trunc is True
        assert self.MyFields.field_profile[STRING_COL].value_trunc is True
        assert self.MyFields.field_profile[LOWER_COL].value_trunc is True
        assert self.MyFields.field_profile[UPPER_COL].value_trunc is True


    def test_field_profile_values(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields()

        assert self.MyFields.field_profile[INT_COL].value_min == 0
        assert self.MyFields.field_profile[STRING_COL].value_min == 'A'
        assert self.MyFields.field_profile[LOWER_COL].value_min == 'bbb'
        assert self.MyFields.field_profile[UPPER_COL].value_min == 'BBB'
        assert self.MyFields.field_profile[EMPTY_COL].value_min is None
        assert self.MyFields.field_profile[FLOAT_COL].value_min == 0.0
        assert self.MyFields.field_profile[MIXED_COL].value_min == 'MIXED'

        assert self.MyFields.field_profile[INT_COL].value_max == 10
        assert self.MyFields.field_profile[STRING_COL].value_max == 'C' # lower d is after uppers
        assert self.MyFields.field_profile[LOWER_COL].value_max == 'ccccc'
        assert self.MyFields.field_profile[EMPTY_COL].value_max is None
        assert self.MyFields.field_profile[FLOAT_COL].field_type == 'float'
        assert self.MyFields.field_profile[FLOAT_COL].value_max == 144.9
        assert self.MyFields.field_profile[MIXED_COL].value_max == 'mixed'

        assert self.MyFields.field_profile[INT_COL].field_type == 'integer'
        assert self.MyFields.field_profile[STRING_COL].field_type == 'string'
        assert self.MyFields.field_profile[EMPTY_COL].field_type == 'unknown'
        assert self.MyFields.field_profile[FLOAT_COL].field_type == 'float'

        assert self.MyFields.field_profile[INT_COL].value_trunc is False
        assert self.MyFields.field_profile[STRING_COL].value_trunc is False
        assert self.MyFields.field_profile[EMPTY_COL].value_trunc is False
        assert self.MyFields.field_profile[FLOAT_COL].value_trunc is False


    def test_string_dictionaries(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields()

        assert self.MyFields.field_profile[STRING_COL].value_case == 'upper'
        assert self.MyFields.field_profile[LOWER_COL].value_case == 'lower'
        assert self.MyFields.field_profile[UPPER_COL].value_case == 'upper'
        assert self.MyFields.field_profile[UPPER_COL].value_max_length == 5
        assert self.MyFields.field_profile[UPPER_COL].value_min_length == 3
        assert self.MyFields.field_profile[UPPER_COL].value_mean_length == 3.727272727272727


    def test_numeric_dictionaries(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields()

        assert self.MyFields.field_profile[INT_COL].value_mean == 5
        assert self.MyFields.field_profile[FLOAT_COL].value_mean == 24.76109090909091
        assert self.MyFields.field_profile[INT_COL].value_median == 5
        assert self.MyFields.field_profile[INT_COL].value_variance == 10
        assert self.MyFields.field_profile[INT_COL].value_stddev == 3.1622776601683795


    def test_timestamp_dictionaries(self):
        assert 1 == 1


    def test_field_names(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields()

        assert self.MyFields.field_profile[INT_COL].field_name == 'field_0'
        assert self.MyFields.field_profile[STRING_COL].field_name == 'field_1'
        assert self.MyFields.field_profile[LOWER_COL].field_name == 'field_2'
        assert self.MyFields.field_profile[UPPER_COL].field_name == 'field_3'
        assert self.MyFields.field_profile[EMPTY_COL].field_name == 'field_4'
        assert self.MyFields.field_profile[FLOAT_COL].field_name == 'field_5'
        assert self.MyFields.field_profile[MIXED_COL].field_name == 'field_6'




class TestBasicCSV(FileAndTestManager):
    """ Test with Non-Quoted CSV File
    """
    def customSettings(self):
        self.quoting = False
        self.header = False
        self.overrides = None


class TestFieldNamesWithHeader(FileAndTestManager):
    """ Test with Non-Quoted CSV File
    """
    def customSettings(self):
        self.header = True
        self.overrides = {}

    def test_field_names(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields()

        assert self.MyFields.field_profile[INT_COL].field_name == 'int'
        assert self.MyFields.field_profile[STRING_COL].field_name == 'string'
        assert self.MyFields.field_profile[LOWER_COL].field_name == 'lower'
        assert self.MyFields.field_profile[UPPER_COL].field_name == 'upper'
        assert self.MyFields.field_profile[EMPTY_COL].field_name == 'empty'
        assert self.MyFields.field_profile[FLOAT_COL].field_name == 'float'
        assert self.MyFields.field_profile[MIXED_COL].field_name == 'mixed'



class TestOverrideFloatToString(FileAndTestManager):
    """ Override Float to String
    """
    def customSettings(self):
        self.quoting = True
        self.header = False
        self.overrides = {5:'string'}

    def test_field_float_overriden_by_string(self):

        self.MyFields = mod.RecordProfiler(input_handler=self.input_handler,
                                           field_cnt=self.field_cnt,
                                           dialect=self.dialect,
                                           verbosity='quiet')
        self.MyFields.analyze_fields(field_types_overrides=self.overrides)

        with pytest.raises(AttributeError):
            assert self.MyFields.field_profile[FLOAT_COL].value_mean is None

        assert self.MyFields.field_profile[FLOAT_COL].value_min == '0.0'
        assert self.MyFields.field_profile[FLOAT_COL].value_max == '99'
        assert self.MyFields.field_profile[FLOAT_COL].field_type == 'string'
        assert self.MyFields.field_profile[FLOAT_COL].value_trunc is False
        assert self.MyFields.field_profile[FLOAT_COL].value_case == 'unknown'
        assert self.MyFields.field_profile[FLOAT_COL].value_max_length == 5
        assert self.MyFields.field_profile[FLOAT_COL].value_min_length == 1
        assert self.MyFields.field_profile[FLOAT_COL].value_mean_length == 3.4545454545454546



def generate_test_file(dialect, record_cnt):
    """ generic file generator used by multiple test classes
    """
    assert dialect.delimiter == ','
    assert dialect.quoting == csv.QUOTE_NONE

    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w")

    if dialect.has_header:
        fp.write("int,string,lower,upper,empty,float,mixed\n")
 
    fp.write("0,A,bbb,BBB,,3.2,mixed\n")
    fp.write("1,B,bbb,BBB,,8.07,MIXED\n")
    fp.write("2,C,bbb,BBB,,0.001,miXED\n")
    fp.write("3,A,bbb,BBB,,13.1,MIXed\n")
    fp.write("4,A,bbb,BBB,,2,mixed\n")
    fp.write("5,A,bbb,BBB,,0.1,MIXED\n")
    fp.write("6,B,bbb,BBB,,0.0,mixed\n")
    fp.write("7,C,ccccc,CCCCC,,144.9,mIXEd\n")
    fp.write("8,A,ccccc,CCCCC,,0.001,MIXED\n")
    fp.write("9,B,ccccc,CCCCC,,2.0,MIXED\n")
    fp.write("10,C,ccccc,CCCCC,,99,MixeD\n")

    fp.close()
    return fqfn
