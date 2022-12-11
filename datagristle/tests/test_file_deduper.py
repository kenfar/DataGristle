#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2015,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import tempfile
import shutil
import fileinput
import csv
from os.path import dirname
from os.path import isfile
from os.path import join as pjoin

import datagristle.file_deduper         as mod
from datagristle.csvhelper import Dialect


class TestDeduping(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.fqfn = create_test_file(self.temp_dir)
        self.dialect = Dialect(delimiter=',', quoting=csv.QUOTE_NONE, has_header=False,
                               quotechar='"', doublequote=False, escapechar=None,
                               skipinitialspace=False)
        self.out_dir = tempfile.mkdtemp(prefix='gristle_out_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.out_dir)

    def test_dedup_file_1key_with_dups(self):
        sorted_fqfn = create_sorted_test_file(self.temp_dir)
        joinfields = [1]
        deduper = mod.CSVDeDuper(self.dialect, joinfields, self.temp_dir)
        (out_fqfn, read_cnt, write_cnt) = deduper.dedup_file(sorted_fqfn)
        assert out_fqfn == self.fqfn + '.uniq'
        assert read_cnt > write_cnt
        for rec in fileinput.input(out_fqfn):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '4'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            else:
                assert 0, "too many rows returned"
        fileinput.close()

    def test_dedup_file_1key_with_empty_file(self):
        input_fqfn = create_empty_test_file(self.temp_dir)
        joinfields = [1]
        deduper = mod.CSVDeDuper(self.dialect, joinfields, self.temp_dir)
        (out_fqfn, read_cnt, write_cnt) = deduper.dedup_file(input_fqfn)
        assert out_fqfn == self.fqfn + '.uniq'
        assert isfile(out_fqfn)
        assert read_cnt == 0
        assert write_cnt == 0

    def test_dedup_file_2keys_without_dups(self):
        sorted_fqfn = create_sorted_test_file(self.temp_dir)
        joinfields = [1, 2]
        deduper = mod.CSVDeDuper(self.dialect, joinfields, self.temp_dir)
        (out_fqfn, read_cnt, write_cnt) = deduper.dedup_file(sorted_fqfn)
        assert out_fqfn == self.fqfn + '.uniq'
        assert read_cnt == write_cnt
        for rec in fileinput.input(out_fqfn):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '4'
            elif fileinput.lineno() == 2:
                assert fields[0] == '3'
            elif fileinput.lineno() == 3:
                assert fields[0] == '2'
            elif fileinput.lineno() == 4:
                assert fields[0] == '1'
            else:
                assert 0, "too many rows returned"
        fileinput.close()

    def test_dedup_file_2keys_with_dups(self):
        sorted_fqfn = create_sorted_file_2keys_dups(self.temp_dir)
        joinfields = [1, 2]
        sorter = mod.CSVDeDuper(self.dialect, joinfields, self.temp_dir)
        (out_fqfn, read_cnt, write_cnt) = sorter.dedup_file(sorted_fqfn)
        assert out_fqfn == self.fqfn + '.uniq'
        assert read_cnt > write_cnt
        for rec in fileinput.input(out_fqfn):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '4'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            else:
                assert 0, "too many rows returned"
        fileinput.close()

    def test_dedup_outfile(self):
        sorted_fqfn = create_sorted_file_2keys_dups(self.temp_dir)
        joinfields = [1, 2]
        sorter = mod.CSVDeDuper(self.dialect, joinfields, self.out_dir)
        (out_fqfn, read_cnt, write_cnt) = sorter.dedup_file(sorted_fqfn)
        assert dirname(out_fqfn) == self.out_dir

def create_empty_test_file(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        pass
    return fqfn

def create_test_file(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        f.write('4, aaa, a23\n')
        f.write('2, bbb, a23\n')
        f.write('1, bbb, b23\n')
        f.write('3, aaa, b23\n')
    return fqfn

def create_sorted_test_file(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        f.write('4, aaa, a23\n')
        f.write('3, aaa, b23\n')
        f.write('2, bbb, a23\n')
        f.write('1, bbb, b23\n')
    return fqfn

def create_sorted_file_2keys_dups(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        f.write('4, aaa, a23\n')
        f.write('3, aaa, a23\n')
        f.write('2, bbb, b23\n')
        f.write('1, bbb, b23\n')
    return fqfn

def get_file_rec_cnt(fqfn):
    rec_cnt = 0
    for rec in fileinput.input(fqfn):
        rec_cnt += 1
    fileinput.close()
    return rec_cnt
