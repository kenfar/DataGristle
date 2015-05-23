#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""
import sys
import os
import tempfile
import random
import atexit
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.file_type  as mod



class Testget_quote_number(object):

    def test_lowercase(self):
        assert mod.get_quote_number('quote_minimal') == 0
        assert mod.get_quote_number('quote_all')  == 1
        assert mod.get_quote_number('quote_none') == 3
        assert mod.get_quote_number('quote_nonnumeric') == 2

    def test_uppercase(self):
        assert mod.get_quote_number('quote_minimal') \
               == mod.get_quote_number('QUOTE_MINIMAL')

    def test_number(self):
        assert mod.get_quote_number(3) == 3
        assert mod.get_quote_number('3') == 3

    def test_none(self):
        assert mod.get_quote_number(None) is None

    def test_nonmatch(self):
        with pytest.raises(ValueError):
            mod.get_quote_number('quote_alot')


class Testget_quote_name(object):

    def test_number(self):
        assert mod.get_quote_name(0) == 'QUOTE_MINIMAL'

    def test_string(self):
        assert mod.get_quote_name('0') == 'QUOTE_MINIMAL'

    def test_none(self):
        with pytest.raises(ValueError):
            mod.get_quote_name(None)

    def test_text(self):
        with pytest.raises(ValueError):
            mod.get_quote_name('QUOTE_MINIMAL')

    def test_bad_number(self):
        with pytest.raises(ValueError):
            mod.get_quote_name(99)



class TestQuotedCSV(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter     = '|'
        self.quoting       = True
        self.test1_fqfn    = generate_test_file1(self.delimiter, 
                                                 self.quoting, self.record_cnt)
        # run FileTyper without csv dialect info:
        self.MyTest        = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_file_misc(self):
        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.csv_quoting == self.quoting


class TestNonQuotedCSV(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter     = '|'
        self.quoting       = True
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, 
                          self.record_cnt)
        self.MyTest     = mod.FileTyper(self.test1_fqfn, None, None, None)
        self.MyTest.analyze_file()

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_file_misc(self):
        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.csv_quoting == self.quoting


class TestInternals(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter     = '|'
        self.quoting       = False
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, 
                          self.record_cnt)
        self.MyTest     = mod.FileTyper(self.test1_fqfn, None, None, None)
        self.MyTest.analyze_file()

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_file_record_number_without_read_limit(self):
        assert (self.record_cnt, False) == self.MyTest._count_records()

    def test_file_record_number_with_read_limit(self):
        self.MyTest = mod.FileTyper(self.test1_fqfn, read_limit=10)
        self.MyTest.analyze_file()
        (est_rec_cnt, est_flag) = self.MyTest._count_records()
        assert est_flag is True
        # it should normally be within 5-10% of 100
        assert abs(115-est_rec_cnt) < 30

    def test_file_format_type(self):
        assert self.MyTest._get_format_type() == 'csv'



def generate_test_file1(delim, quoting, record_cnt):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w") 
    name_list = ['smith','jones','thompson','ritchie']
    role_list = ['pm','programmer','dba','sysadmin','qa','manager']
    proj_list = ['cads53','jefta','norma','us-cepa']

    for i in range(record_cnt):
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        if quoting is True:
           name = '"' + name + '"'
           role = '"' + role + '"'
           proj = '"' + proj + '"'
        record = '''%(i)s%(delim)s%(proj)s%(delim)s%(role)s%(delim)s%(name)s\n''' % locals()
        fp.write(record)

    fp.close()
    return fqfn
