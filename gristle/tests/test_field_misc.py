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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.field_misc  as mod




class Test_get_case(object):

    def setup_method(self, method):
        self.test_u1 = ['AAA','BBB','CCC']
        self.test_u2 = ['AAA','BBB','CCC','$B']
        self.test_u2 = ['AAA','BBB','CCC','D`~!@#$%^&*()-+=[{]}']

        self.test_m1 = ['aaa','bbb','ccc']
        self.test_m2 = ['aaa','BBB','ccc']

        self.test_unk1 = ['111','222','333']
        self.test_unk2 = []


    def test_misc_basics(self):
        assert mod.get_case('string', self.test_u1) == 'upper'
        assert mod.get_case('string', self.test_u2) == 'upper'

        assert mod.get_case('string', self.test_m1) == 'lower'
        assert mod.get_case('string', self.test_m2) == 'mixed'

        assert mod.get_case('string', self.test_unk1) == 'unknown'
        assert mod.get_case('string', self.test_unk2) == 'unknown'



class Test_get_field_freq(object):

    def setup_method(self, method):
        (fd1, self.test1_fqfn) = tempfile.mkstemp()
        fp1 = os.fdopen(fd1, "w")
        for x in range(100):
            reca = 'a%d|a%d|\n' % (x, x)
            fp1.write(reca)
            recb = 'b%d|b%d|\n' % (x, x)
            fp1.write(recb)
        fp1.close()

        self.dialect                  = csv.Dialect
        self.dialect.delimiter        = '|'
        self.dialect.skipinitialspace = False
        self.dialect.quoting          = False           #naive default!
        self.dialect.quotechar        = '"'             #naive default!
        self.dialect.lineterminator   = '\n'            #naive default!
        self.dialect.has_header       = False

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_misc_truncation(self):
        (freq, trunc_flag, bad_cnt) = mod.get_field_freq(self.test1_fqfn,
                                                self.dialect,
                                                field_number=0,
                                                max_freq_size=4)
        assert len(freq) == 4
        assert trunc_flag is True

    def test_misc_no_trunc_high_cardinality(self):
        (freq, trunc_flag, bad_cnt) = mod.get_field_freq(self.test1_fqfn,
                                                self.dialect,
                                                field_number=0)
        assert len(freq) == 200
        assert trunc_flag is False

    def test_misc_no_trunc_low_cardinality(self):
        (freq, trunc_flag, bad_cnt) = mod.get_field_freq(self.test1_fqfn,
                                                self.dialect,
                                                field_number=2)
        assert len(freq) == 1  # should be 1 x '' x 200 occurances
        assert trunc_flag is False

    def test_misc_read_limit_truncation(self):
        (freq, trunc_flag, bad_cnt) = mod.get_field_freq(self.test1_fqfn,
                                                         self.dialect,
                                                         field_number=0,
                                                         max_freq_size=-1,
                                                         read_limit=10)
        assert len(freq) == 11
        assert trunc_flag is True




class TestGetFieldNames(object):

    def setup_method(self, method):
        header_rec           = '"name","phone","gender","age"\n'
        data_rec             = '"ralph","719-555-1212","m","39"\n'

        noquote_header_rec   = 'name,phone,gender,age\n'
        noquote_data_rec     = 'ralph,719-555-1212,m,39\n'

        self.name_list       = ['name','phone','gender','age']

        self.dialect                  = csv.Dialect
        self.dialect.delimiter        = ','
        self.dialect.skipinitialspace = False
        self.dialect.quoting          = True            #naive default!
        self.dialect.quotechar        = '"'             #naive default!
        self.dialect.lineterminator   = '\n'            #naive default!
        self.dialect.has_header       = True

        (fd1, self.header_fqfn) = tempfile.mkstemp()
        fp1 = os.fdopen(fd1,"w")
        fp1.write(header_rec)
        fp1.write(data_rec)
        fp1.close()

        (fd2, self.headless_fqfn) = tempfile.mkstemp()
        fp2 = os.fdopen(fd2,"w")
        fp2.write(data_rec)
        fp2.close()

        (fd3, self.empty_fqfn) = tempfile.mkstemp()
        fp3 = os.fdopen(fd3,"w")
        fp3.close()

        (fd4, self.noquote_fqfn) = tempfile.mkstemp()
        fp4 = os.fdopen(fd4,"w")
        fp4.write(noquote_header_rec)
        fp4.write(noquote_data_rec)
        fp4.close()


    def teardown_method(self, method):
        os.remove(self.header_fqfn)
        os.remove(self.headless_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.noquote_fqfn)

    def test_misc_header_all_cols(self):

        assert mod.get_field_names(self.header_fqfn,
                                   self.dialect) == self.name_list

    def test_misc_header_one_col(self):

        assert mod.get_field_names(self.header_fqfn, 
                                   self.dialect, 1)  == 'phone'

    def test_misc_headless_all_col(self):
        self.dialect.has_header = False
        assert mod.get_field_names(self.headless_fqfn, self.dialect) \
                == ['field_0','field_1','field_2','field_3']

    def test_misc_headless_one_col(self):
        self.dialect.has_header = False
        assert mod.get_field_names(self.headless_fqfn, self.dialect, 1) \
                == 'field_1'

    def test_misc_empty(self):
        # test with header:
        assert mod.get_field_names(self.empty_fqfn, self.dialect) is None
        assert mod.get_field_names(self.empty_fqfn, self.dialect, 1) is None

        # test without header
        self.dialect.has_header = False
        assert mod.get_field_names(self.empty_fqfn, self.dialect) is None
        assert mod.get_field_names(self.empty_fqfn, self.dialect, 1) is None

    def test_misc_noquote(self):

        assert mod.get_field_names(self.noquote_fqfn,
                                   self.dialect) == self.name_list
        assert mod.get_field_names(self.noquote_fqfn,
                                   self.dialect, 1) == 'phone'
        #print mod.get_field_names(self.noquote_fqfn, self.dialect) 


class TestMinAndMax(object):

    def setup_method(self, method):
        self.empty_dict  = {}
        self.empty_list  = []
        self.easy_dict   = {'Wyoming': 3,
                            'Nevada':  2,
                            'Texas':   4}
        self.easy_list   = ['Wyoming',
                            'Nevada',
                            'Texas' ]
        self.unk_list    = ['UNK',
                            'unknown',
                            ' ',
                            'Nevada',
                            'Texas' ]
        self.unk_dict    = {'UNK':1    ,
                            'unknown':3,
                            ' ':99     ,
                            'Nevada':4 ,
                            'Texas': 4}
        self.num_dict    = {'9':1      ,
                            '202':3    ,
                            ' ':99     ,
                            '51':4     ,
                            '777':2    ,
                            '11':2 }

    def test_misc_emptiness(self):
        assert mod.get_max('string', self.empty_dict) is None
        assert mod.get_max('string', self.empty_list) is None
        assert mod.get_min('string', self.empty_dict) is None
        assert mod.get_min('string', self.empty_list) is None

    def test_misc_easy_dict(self):
        assert mod.get_max('string', self.easy_dict)  == 'Wyoming'
        assert mod.get_min('string', self.easy_dict)  == 'Nevada'

    def test_misc_easy_list(self):
        assert mod.get_max('string', self.easy_list)  == 'Wyoming'
        assert mod.get_min('string', self.easy_list)  == 'Nevada'

    def test_misc_unknowns(self):
        assert mod.get_max('string', self.unk_list)  == 'Texas'
        assert mod.get_max('string', self.unk_dict)  == 'Texas'
        assert mod.get_min('string', self.unk_dict)  == 'Nevada'
        assert mod.get_min('string', self.unk_list)  == 'Nevada'

    def test_misc_mins(self):
        assert mod.get_min('integer', self.num_dict)  == '9'




