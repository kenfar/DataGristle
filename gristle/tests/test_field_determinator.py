#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import random
import csv
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.field_determinator  as mod



def generate_test_file(delim, record_cnt, quoting):
    """ generic file generator used by multiple test classes
    """
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w")

    for i in range(record_cnt):
        fields = []

        fields.append(str(i))                         # field 0: id_col

        if i % 4 == 0:                                # field 1: very mixed col
           fields.append('A')
        elif i % 5 == 0:
           fields.append('b')
        elif i % 3 == 0:
           fields.append('C')
        elif i % 2 == 0:
           fields.append('d')
        else:
           fields.append('E')
        #print '%d - %s' % (i, fields[len(fields)-1]) 

        fields.append('bbbbb')                        # field 2: lower col
        fields.append('CCC')                          # field 3: upper col
        fields.append('')                             # field 4: empty col
        fields.append('999.9')                        # field 5: float col
        fields.append('aaa')                          # field 6: extra string col
        outrec = delim.join(fields)+'\n'
        fp.write(outrec)

    fp.close()
    return fqfn



class FileAndTestManager(object):
    """ Generic Test Class
    """

    def print_field(self, field_no):
        print 'type:      %s' % self.MyFields.field_types[field_no]
        #print 'int mean:: %f' % self.MyFields.field_mean[field_no]
        print 'freq:     '
        print self.MyFields.field_freqs[field_no]

    def customSettings(self):
        """ gets run from setup_method()
        """
        self.quoting                  = False
        self.overrides                = None

    def setup_method(self, method):
   
        self.customSettings()

        self.record_cnt               = 100
        self.dialect                  = csv.Dialect
        self.dialect.quoting          = self.quoting
        self.dialect.quotechar        = '"'      
        self.dialect.has_header       = False
        self.dialect.delimiter        = '|'
        self.dialect.skipinitialspace = False
        self.dialect.lineterminator   = '\n'   
        self.format_type              = 'csv'
        self.field_cnt                = 7
        self.test1_fqfn    = generate_test_file(self.dialect.delimiter, 
                                                self.record_cnt,
                                                self.dialect.quoting)
        self.id_col                   = 0
        self.very_mixed_col           = 1
        self.lower_col                = 2
        self.upper_col                = 3
        self.empty_col                = 4
        self.float_col                = 5
        self.string_col               = 6

        # run FileTyper without csv dialect info:
        self.MyFields = mod.FieldDeterminator(self.test1_fqfn,
                                  self.format_type       ,
                                  self.field_cnt         ,
                                  self.dialect.has_header,
                                  self.dialect           ,
                                  self.dialect.delimiter ,
                                  rec_delimiter = None   ,
                                  verbose       = False  )

        self.MyFields.analyze_fields(None, self.overrides)
        #self.print_field(self.float_col)

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)


    def test_deter_a01_field_freq(self):

        # there are 100 unique values for this column
        assert len(self.MyFields.get_known_values(self.id_col)) == 100

        # there are about 5 values for this column, show just 2
        assert len(self.MyFields.get_top_freq_values(fieldno=1, limit=2)) == 2

        # there is only one value for these columns:
        assert len(self.MyFields.get_top_freq_values(fieldno=3, limit=2)) == 1
        assert len(self.MyFields.get_top_freq_values(fieldno=5, limit=2)) == 1
        assert len(self.MyFields.get_top_freq_values(fieldno=6, limit=2)) == 1

        # this is an empty field - it should show up as a single value with 
        # occurance of 100
        assert len(self.MyFields.get_top_freq_values(fieldno=4, limit=2)) == 1

        # given a large file (> 15 entries) E becomes the most common value
        assert self.MyFields.get_top_freq_values(fieldno=1, limit=1)[0][0] == 'E'

        # check actual values coming back:
        assert self.MyFields.get_top_freq_values(fieldno=5, limit=1)[0][0] == '999.9'
        assert self.MyFields.get_top_freq_values(fieldno=6, limit=1)[0][0] == 'aaa'


    def test_deter_a02_field_general_dictionaries(self):
        assert self.MyFields.field_min[self.id_col]             == '0'
        assert self.MyFields.field_min[self.very_mixed_col]     == 'A'
        assert self.MyFields.field_min[self.lower_col]          == 'bbbbb'
        assert self.MyFields.field_min[self.empty_col]          is None
        assert self.MyFields.field_min[self.float_col]          == '999.9'
        assert self.MyFields.field_min[self.string_col]         == 'aaa'

        assert self.MyFields.field_max[self.id_col]             == '99'
        assert self.MyFields.field_max[self.very_mixed_col]     == 'd'   # lower d is after uppers
        assert self.MyFields.field_max[self.lower_col]          == 'bbbbb'
        assert self.MyFields.field_max[self.empty_col]          is None
        assert self.MyFields.field_max[self.float_col]          == '999.9'
        assert self.MyFields.field_max[self.string_col]         == 'aaa'

        assert self.MyFields.field_types[self.id_col]           == 'integer'
        assert self.MyFields.field_types[self.very_mixed_col]   == 'string'
        assert self.MyFields.field_types[self.empty_col]        == 'unknown'
        assert self.MyFields.field_types[self.float_col]        == 'float'
        assert self.MyFields.field_types[self.string_col]       == 'string'

        assert self.MyFields.field_trunc[self.id_col]           is False
        assert self.MyFields.field_trunc[self.very_mixed_col]   is False
        assert self.MyFields.field_trunc[self.empty_col]        is False
        assert self.MyFields.field_trunc[self.float_col]        is False
        assert self.MyFields.field_trunc[self.string_col]       is False


    def test_deter_a03_field_string_dictionaries(self):
        assert self.MyFields.field_case[self.id_col]                 is None
        assert self.MyFields.field_case[self.very_mixed_col]         == 'mixed'
        assert self.MyFields.field_case[self.lower_col]              == 'lower'
        assert self.MyFields.field_case[self.upper_col]              == 'upper'
        assert self.MyFields.field_case[self.empty_col]              is None
        assert self.MyFields.field_case[self.float_col]              is None
        assert self.MyFields.field_case[self.string_col]             == 'lower'

        assert self.MyFields.field_max_length[self.id_col]           is None
        assert self.MyFields.field_max_length[self.upper_col]        == 3
        assert self.MyFields.field_max_length[self.empty_col]        is None
        assert self.MyFields.field_max_length[self.float_col]        is None
        assert self.MyFields.field_max_length[self.string_col]       == 3

        assert self.MyFields.field_min_length[self.id_col]           is None
        assert self.MyFields.field_min_length[self.upper_col]        == 3
        assert self.MyFields.field_min_length[self.empty_col]        is None
        assert self.MyFields.field_min_length[self.float_col]        is None
        assert self.MyFields.field_min_length[self.string_col]       == 3

        assert self.MyFields.field_mean_length[self.id_col]          is None
        assert self.MyFields.field_mean_length[self.upper_col]       == 3
        assert self.MyFields.field_mean_length[self.empty_col]       is None
        assert self.MyFields.field_mean_length[self.float_col]       is None
        assert self.MyFields.field_mean_length[self.string_col]      == 3


    def test_deter_a04_field_numeric_dictionaries(self):
        assert self.MyFields.field_mean[self.id_col]
        assert self.MyFields.field_mean[self.very_mixed_col]    is None
        assert self.MyFields.field_mean[self.empty_col]         is None
        assert self.MyFields.field_mean[self.float_col]
        assert self.MyFields.field_mean[self.string_col]        is None

        assert self.MyFields.field_median[self.id_col]
        assert self.MyFields.field_median[self.very_mixed_col]  is None
        assert self.MyFields.field_median[self.empty_col]       is None
        assert self.MyFields.field_median[self.string_col]      is None

        assert self.MyFields.variance[self.id_col]
        assert self.MyFields.variance[self.very_mixed_col]      is None
        assert self.MyFields.variance[self.empty_col]           is None
        assert self.MyFields.variance[self.string_col]          is None

        assert self.MyFields.stddev[self.id_col]
        assert self.MyFields.stddev[self.very_mixed_col]        is None
        assert self.MyFields.stddev[self.empty_col]             is None
        assert self.MyFields.stddev[self.string_col]            is None


    def test_deter_a05_field_5_extra_float(self):
        """ 
        """
        ####print self.MyFields.get_top_freq_values(fieldno=5, limit=10)
        assert self.MyFields.field_mean[self.float_col]               is not None

    def test_deter_a06_field_6_extra_string(self):
        assert self.MyFields.field_mean[self.string_col]  is None
        assert self.MyFields.field_mean[self.string_col]  is None


class TestQuotedCSV(FileAndTestManager):
    """ Test with Quoted CSV File
    """
    def customSettings(self):
        self.quoting     = True
        self.overrides   = None


class TestNonQuotedCSV(FileAndTestManager):
    """ Test with Non-Quoted CSV File
    """
    def customSettings(self):
        self.quoting     = False
        self.overrides   = None


class TestOverrideFloatToString(FileAndTestManager):
    """ Override Float to String 
    """
    def customSettings(self):
        self.quoting     = True
        self.overrides   = {5:'string'}

    def test_deter_a05_field_5_extra_float(self):
        assert self.MyFields.field_mean[self.float_col]               is None

    def test_deter_a02_field_general_dictionaries(self):
        assert self.MyFields.field_min[self.float_col]          == '999.9'
        assert self.MyFields.field_max[self.float_col]          == '999.9'
        assert self.MyFields.field_types[self.float_col]        == 'string'
        assert self.MyFields.field_trunc[self.float_col]        == False

    def test_deter_a03_field_string_dictionaries(self):
        assert self.MyFields.field_case[self.float_col]         is not None
        assert self.MyFields.field_max_length[self.float_col]   is not None
        assert self.MyFields.field_min_length[self.float_col]   is not None
        assert self.MyFields.field_mean_length[self.float_col]  is not None

    def test_deter_a04_field_numeric_dictionaries(self):
        assert self.MyFields.field_mean[self.float_col]         is None



