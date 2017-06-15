#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import sys
import tempfile
import random
import csv
import os
from os.path import dirname

import pytest

import datagristle.file_type  as mod



class Testget_quote_number(object):

    def test_lowercase(self):
        assert mod.get_quote_number('quote_minimal') == 0
        assert mod.get_quote_number('quote_all') == 1
        assert mod.get_quote_number('quote_none') == 3
        assert mod.get_quote_number('quote_nonnumeric') == 2

    def test_uppercase(self):
        assert mod.get_quote_number('quote_minimal') \
               == mod.get_quote_number('QUOTE_MINIMAL')

    def test_number(self):
        with pytest.raises(ValueError):
            assert mod.get_quote_number(3) == 3
        with pytest.raises(ValueError):
            assert mod.get_quote_number('3') == 3

    def test_nonmatch(self):
        with pytest.raises(ValueError):
            mod.get_quote_number('quote_alot')

    def test_none(self):
        with pytest.raises(ValueError):
            mod.get_quote_number(None)


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



class TestQuotingFromFile(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter = '|'

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_quote_minimal(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_MINIMAL, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_MINIMAL

    def test_quote_all(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_ALL, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_ALL

    def test_quote_none(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_NONE, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_NONE



class TestQuotingFromOverrides(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter = '|'

    def teardown_method(self, method):
        os.remove(self.test1_fqfn)

    def test_quote_minimal(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_MINIMAL, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn, delimiter=self.delimiter, quoting='QUOTE_MINIMAL')
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_MINIMAL

    def test_quote_all(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_ALL, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn, delimiter=self.delimiter, quoting='QUOTE_ALL')
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_ALL

    def test_quote_none(self):
        self.test1_fqfn = generate_test_file1(self.delimiter, csv.QUOTE_NONE, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn, delimiter=self.delimiter, quoting='QUOTE_NONE')
        self.MyTest.analyze_file()

        assert self.MyTest.record_cnt == self.record_cnt
        assert self.MyTest.field_cnt == 4
        assert self.MyTest.format_type == 'csv'
        assert self.MyTest.dialect.delimiter == self.delimiter
        assert self.MyTest.dialect.quoting == csv.QUOTE_NONE



class TestInternals(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.delimiter = '|'
        self.quoting = False
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, self.record_cnt)
        self.MyTest = mod.FileTyper(self.test1_fqfn, None, None, None)
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
    fp = os.fdopen(fd, "w")
    name_list = ['smith', 'jones', 'thompson', 'ritchie']
    role_list = ['pm', 'programmer', 'dba', 'sysadmin', 'qa', 'manager']
    proj_list = ['cads53', 'jefta', 'norma', 'us-cepa']

    for i in range(record_cnt):
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        if quoting in (csv.QUOTE_MINIMAL, csv.QUOTE_ALL):
            name = '"' + name + '"'
            role = '"' + role + '"'
            proj = '"' + proj + '"'
        num = i
        if quoting == csv.QUOTE_ALL:
            num = '"' + str(i) + '"'
        record = f'''{num}{delim}{proj}{delim}{role}{delim}{name}\n'''
        #print(record)
        fp.write(record)

    fp.close()
    return fqfn
