#!/usr/bin/env python

# standard modules:
import sys
import os
import copy
import time
import tempfile
import shutil
import gzip
import fileinput
import csv

from os.path import dirname, basename
from os.path import isfile, isdir, exists
from os.path import join as pjoin

# third-party modules:
import envoy
import pytest
from pprint import pprint as pp


# foo modules:
sys.path.insert(0, dirname('../'))
sys.path.insert(0, dirname('../../'))
sys.path.append('../../../../')

import gristle.file_sorter          as mod
from gristle.csvhelper import create_dialect


class TestSort(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.dialect  = create_dialect(delimiter=',', quoting=csv.QUOTE_NONE, hasheader=False) 
        self.fqfn     = create_test_file(self.temp_dir)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_sort_file_invalid_inputs(self):
        with pytest.raises(AssertionError):
            sorter  = mod.CSVSorter(self.dialect, None)
        sorter  = mod.CSVSorter(self.dialect, '3')
        with pytest.raises(ValueError):
            sorter.sort_file('/tmp/thisfiledoesnotexist.csv')

    def test_sort_file_numeric(self):
        join_fields = '0'
        sorter  = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile  = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(',')
            print fields
            if fileinput.lineno() == 1:
                assert fields[0] == '1'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            elif fileinput.lineno() == 3:
                assert fields[0] == '3'
            elif fileinput.lineno() == 4:
                assert fields[0] == '4'
            else:
                assert 0, 'too many rows returned'
        fileinput.close()

    def test_sort_file_with_tab_delimiter(self):
        join_fields = '0'
        self.dialect.delimiter = '\t'
        self.fqfn     = create_test_file(self.temp_dir, self.dialect.delimiter)
        sorter  = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile  = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(self.dialect.delimiter)
            print fields
            if fileinput.lineno() == 1:
                assert fields[0] == '1'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            elif fileinput.lineno() == 3:
                assert fields[0] == '3'
            elif fileinput.lineno() == 4:
                assert fields[0] == '4'
            else:
                assert 0, 'too many rows returned'
        fileinput.close()

    def test_sort_file_alpha_combo(self):
        join_fields   = [1, 2]
        sorter        = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile       = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(',')
            print fields
            if fileinput.lineno() == 1:
                assert fields[0] == '4'
            elif fileinput.lineno() == 2:
                assert fields[0] == '3'
            elif fileinput.lineno() == 3:
                assert fields[0] == '2'
            elif fileinput.lineno() == 4:
                assert fields[0] == '1'
            else:
                assert 0, 'too many rows returns'
        fileinput.close()

    def test_sort_file_outdir(self):
        out_dir = tempfile.mkdtemp(prefix='gristle_out_')
        join_fields   = [1, 2]
        sorter        = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, out_dir)
        outfile       = sorter.sort_file(self.fqfn)
        assert dirname(outfile) == out_dir
        assert basename(outfile) == basename(self.fqfn) + '.sorted'


def create_test_file(temp_dir, delimiter=','):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        f.write(delimiter.join(['4', 'aaa', 'a23']) + '\n')
        #f.write('4, aaa, a23\n')
        f.write(delimiter.join(['2', 'bbb', 'a23']) + '\n')
        #f.write('2, bbb, a23\n')
        f.write(delimiter.join(['1', 'bbb', 'b23']) + '\n')
        #f.write('1, bbb, b23\n')
        f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
        #f.write('3, aaa, b23\n')
    return fqfn


