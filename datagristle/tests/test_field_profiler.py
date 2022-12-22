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
        self.overrides = None
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
        input_handler = file_io.InputHandler(files=[self.test1_fqfn], dialect=self.dialect)
        self.MyFields = mod.FieldDeterminator(input_handler=input_handler,
                                              field_cnt=self.field_cnt,
                                              dialect=self.dialect,
                                              verbosity='quiet')

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)


    def test_deter_field_freq(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        # there are 100 unique values for this column
        assert len(self.MyFields.get_known_values(INT_COL)) == 11

        # there are 11 values for this column, show just 2
        assert len(self.MyFields.get_top_freq_values(fieldno=INT_COL, limit=2)) == 2

        # there are only 2 values for these columns:
        assert len(self.MyFields.get_top_freq_values(fieldno=LOWER_COL, limit=2)) == 2
        assert len(self.MyFields.get_top_freq_values(fieldno=UPPER_COL, limit=2)) == 2

        # this is an empty field - it should show up as a single value with
        # occurance of 1
        assert len(self.MyFields.get_top_freq_values(fieldno=EMPTY_COL, limit=2)) == 1

        # A is the most common value
        assert self.MyFields.get_top_freq_values(fieldno=STRING_COL, limit=1)[0][0] == 'A'

        # check actual values coming back:
        assert self.MyFields.get_top_freq_values(fieldno=FLOAT_COL, limit=1)[0][0] == '0.001'
        assert self.MyFields.get_top_freq_values(fieldno=LOWER_COL, limit=1)[0][0] == 'bbb'


    def test_read_limit_truncation(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides, read_limit=5)

        # there are 100 unique values for this column normally, this time
        # it should be truncated at 10
        pp('***************************************')
        pp(self.MyFields.get_known_values(INT_COL))
        pp('***************************************')
        assert len(self.MyFields.get_known_values(INT_COL)) == 5
        assert self.MyFields.field_trunc[INT_COL] is True
        assert self.MyFields.field_trunc[STRING_COL] is True
        assert self.MyFields.field_trunc[EMPTY_COL] is True
        assert self.MyFields.field_trunc[FLOAT_COL] is True
        assert self.MyFields.field_trunc[MIXED_COL] is True


    def test_maxfreq_truncation(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides, max_freq_number=7)

        # there are 100 unique values for this column normally, this time
        # only high-cardinality cols should be truncated at 7
        assert len(self.MyFields.get_known_values(INT_COL)) == 7
        assert self.MyFields.field_trunc[INT_COL] is True
        assert len(self.MyFields.get_known_values(FLOAT_COL)) == 7
        assert self.MyFields.field_trunc[FLOAT_COL] is True
        # the rest of these have fewer values in their original data:
        assert self.MyFields.field_trunc[EMPTY_COL] is False
        assert self.MyFields.field_trunc[MIXED_COL] is False
        assert self.MyFields.field_trunc[STRING_COL] is False
        assert self.MyFields.field_trunc[LOWER_COL] is False
        assert self.MyFields.field_trunc[UPPER_COL] is False


    def test_general_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        assert self.MyFields.field_min[INT_COL] == '0'
        assert self.MyFields.field_min[STRING_COL] == 'A'
        assert self.MyFields.field_min[LOWER_COL] == 'bbb'
        assert self.MyFields.field_min[UPPER_COL] == 'BBB'
        assert self.MyFields.field_min[EMPTY_COL] is None
        assert self.MyFields.field_min[FLOAT_COL] == '0.0'
        assert self.MyFields.field_min[MIXED_COL] == 'MIXED'

        assert self.MyFields.field_max[INT_COL] == '10'
        assert self.MyFields.field_max[STRING_COL] == 'C' # lower d is after uppers
        assert self.MyFields.field_max[LOWER_COL] == 'ccccc'
        assert self.MyFields.field_max[EMPTY_COL] is None
        assert self.MyFields.field_types[FLOAT_COL] == 'float'
        assert self.MyFields.field_max[FLOAT_COL] == '144.9'
        assert self.MyFields.field_max[MIXED_COL] == 'mixed'

        assert self.MyFields.field_types[INT_COL] == 'integer'
        assert self.MyFields.field_types[STRING_COL] == 'string'
        assert self.MyFields.field_types[EMPTY_COL] == 'unknown'
        assert self.MyFields.field_types[FLOAT_COL] == 'float'

        assert self.MyFields.field_trunc[INT_COL] is False
        assert self.MyFields.field_trunc[STRING_COL] is False
        assert self.MyFields.field_trunc[EMPTY_COL] is False
        assert self.MyFields.field_trunc[FLOAT_COL] is False


    def test_string_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        assert self.MyFields.field_case[INT_COL] is None
        assert self.MyFields.field_case[STRING_COL] == 'upper'
        assert self.MyFields.field_case[LOWER_COL] == 'lower'
        assert self.MyFields.field_case[UPPER_COL] == 'upper'
        assert self.MyFields.field_case[EMPTY_COL] is None
        assert self.MyFields.field_case[FLOAT_COL] is None

        assert self.MyFields.field_max_length[INT_COL] is None
        assert self.MyFields.field_max_length[UPPER_COL] == 5
        assert self.MyFields.field_max_length[EMPTY_COL] is None  # report 2!
        assert self.MyFields.field_max_length[FLOAT_COL] is None

        assert self.MyFields.field_min_length[INT_COL] is None
        assert self.MyFields.field_min_length[UPPER_COL] == 3
        assert self.MyFields.field_min_length[EMPTY_COL] is None  # reports 2!
        assert self.MyFields.field_min_length[FLOAT_COL] is None

        assert self.MyFields.field_mean_length[INT_COL] is None
        assert self.MyFields.field_mean_length[UPPER_COL] == 3.727272727272727
        assert self.MyFields.field_mean_length[EMPTY_COL] is None  # report 2.0!
        assert self.MyFields.field_mean_length[FLOAT_COL] is None


    def test_numeric_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        assert self.MyFields.field_mean[INT_COL]
        assert self.MyFields.field_mean[STRING_COL] is None
        assert self.MyFields.field_mean[EMPTY_COL] is None
        assert self.MyFields.field_mean[FLOAT_COL]

        assert self.MyFields.field_median[INT_COL]
        assert self.MyFields.field_median[STRING_COL] is None
        assert self.MyFields.field_median[EMPTY_COL] is None

        assert self.MyFields.variance[INT_COL]
        assert self.MyFields.variance[STRING_COL] is None
        assert self.MyFields.variance[EMPTY_COL] is None

        assert self.MyFields.stddev[INT_COL]
        assert self.MyFields.stddev[STRING_COL] is None
        assert self.MyFields.stddev[EMPTY_COL] is None


    def test_timestamp_dictionaries(self):
        assert 1 == 1


    def test_field_names(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        assert self.MyFields.field_names[INT_COL] == 'field_0'
        assert self.MyFields.field_names[STRING_COL] == 'field_1'
        assert self.MyFields.field_names[LOWER_COL] == 'field_2'
        assert self.MyFields.field_names[UPPER_COL] == 'field_3'
        assert self.MyFields.field_names[EMPTY_COL] == 'field_4'
        assert self.MyFields.field_names[FLOAT_COL] == 'field_5'
        assert self.MyFields.field_names[MIXED_COL] == 'field_6'




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
        self.overrides = None

    def test_field_names(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)

        assert self.MyFields.field_names[INT_COL] == 'int'
        assert self.MyFields.field_names[STRING_COL] == 'string'
        assert self.MyFields.field_names[LOWER_COL] == 'lower'
        assert self.MyFields.field_names[UPPER_COL] == 'upper'
        assert self.MyFields.field_names[EMPTY_COL] == 'empty'
        assert self.MyFields.field_names[FLOAT_COL] == 'float'
        assert self.MyFields.field_names[MIXED_COL] == 'mixed'





class TestOverrideFloatToString(FileAndTestManager):
    """ Override Float to String
    """
    def customSettings(self):
        self.quoting = True
        self.header = False
        self.overrides = {5:'string'}

    def test_field_5_extra_float(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)
        assert self.MyFields.field_mean[FLOAT_COL] is None

    def test_general_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)
        assert self.MyFields.field_min[FLOAT_COL] == '0.0'
        assert self.MyFields.field_max[FLOAT_COL] == '99'
        assert self.MyFields.field_types[FLOAT_COL] == 'string'
        assert self.MyFields.field_trunc[FLOAT_COL] is False

    def test_string_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)
        assert self.MyFields.field_case[FLOAT_COL] is not None
        assert self.MyFields.field_max_length[FLOAT_COL] is not None
        assert self.MyFields.field_min_length[FLOAT_COL] is not None
        assert self.MyFields.field_mean_length[FLOAT_COL] is not None

    def test_numeric_dictionaries(self):
        self.MyFields.analyze_fields(None, field_types_overrides=self.overrides)
        assert self.MyFields.field_mean[FLOAT_COL] is None




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
