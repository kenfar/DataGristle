#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import csv
import os
import random
import tempfile

import pytest

import datagristle.csvhelper as csvhelper
import datagristle.file_type as mod




class TestQuotingFromFile(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.field_cnt = 4

    def teardown_method(self, method):
        os.remove(self.test_fqfn)

    def test_quote_minimal(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_MINIMAL, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == self.field_cnt
        assert file_typer.dialect.delimiter == dialect.delimiter
        assert file_typer.dialect.quoting == dialect.quoting

    def test_quote_all(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == self.field_cnt
        assert file_typer.dialect.delimiter == dialect.delimiter
        assert file_typer.dialect.quoting == dialect.quoting

    def test_quote_none(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_NONE, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == self.field_cnt
        assert file_typer.dialect.delimiter == dialect.delimiter
        assert file_typer.dialect.quoting == dialect.quoting




class TestQuotingFromOverrides(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.test_fqfn = None

    def teardown_method(self, method):
        if self.test_fqfn:
            os.remove(self.test_fqfn)

    def test_quote_minimal(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_MINIMAL, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == 4

    def test_quote_all(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == 4

    def test_quote_none(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_NONE, has_header=False)
        self.test_fqfn = generate_test_file1(dialect, self.record_cnt)
        file_typer = mod.FileTyper(dialect, self.test_fqfn)
        file_typer.analyze_file()

        assert file_typer.record_cnt == self.record_cnt
        assert file_typer.field_cnt == 4



class TestInternals(object):

    def setup_method(self, method):
        self.record_cnt = 100
        self.dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_NONE, has_header=False)
        self.test_fqfn = generate_test_file1(self.dialect, self.record_cnt)
        self.file_typer = mod.FileTyper(self.dialect, self.test_fqfn)
        self.file_typer.analyze_file()

    def teardown_method(self, method):
        os.remove(self.test_fqfn)

    def test_file_record_number_without_read_limit(self):
        assert (self.record_cnt, False) == self.file_typer._count_records()

    def test_file_record_number_with_read_limit(self):
        file_typer = mod.FileTyper(self.dialect, self.test_fqfn, read_limit=10)
        file_typer.analyze_file()
        (est_rec_cnt, est_flag) = file_typer._count_records()
        assert est_flag is True
        # it should normally be within 5-10% of 100
        assert abs(115-est_rec_cnt) < 30



def generate_test_file1(dialect, record_cnt):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd, "w")
    name_list = ['smith', 'jones', 'thompson', 'ritchie']
    role_list = ['pm', 'programmer', 'dba', 'sysadmin', 'qa', 'manager']
    proj_list = ['cads53', 'jefta', 'norma', 'us-cepa']

    for i in range(record_cnt):
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        if dialect.quoting in (csv.QUOTE_MINIMAL, csv.QUOTE_ALL):
            name = '"' + name + '"'
            role = '"' + role + '"'
            proj = '"' + proj + '"'
        num = i
        if dialect.quoting == csv.QUOTE_ALL:
            num = '"' + str(i) + '"'
        record = f'''{num}{dialect.delimiter}{proj}{dialect.delimiter}{role}{dialect.delimiter}{name}\n'''
        fp.write(record)

    fp.close()
    return fqfn
