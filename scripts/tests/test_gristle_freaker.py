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
#pylint: disable=empty-docstring

import csv
import os
from os.path import dirname, join as pjoin
import pytest
import random
import sys
import tempfile

import datagristle.test_tools as test_tools
import datagristle.file_io as file_io
import datagristle.csvhelper as csvhelper

pgm_path = dirname(dirname(os.path.realpath((__file__))))
mod = test_tools.load_script(pjoin(pgm_path, 'gristle_freaker'))


class TestBuildFreq(object):

    def setup_method(self, method):
        self.dialect = csv.Dialect
        self.dialect.delimiter = '|'
        self.dialect.quoting = csv.QUOTE_MINIMAL
        self.dialect.quotechar = '"'
        self.dialect.has_header = False
        self.dialect.lineterminator = '\n'
        self.files = []
        self.files.append(generate_test_file(self.dialect.delimiter, 1000))
        self.columns = [1, 2]
        self.col_type = 'specified'
        self.number = 1000
        self.sampling_method = 'non'
        self.sampling_rate = None
        self.sortorder = 'reverse'
        self.sortcol = 1
        self.max_key_len = 50
        self.tempdir = tempfile.mkdtemp(prefix='test_gristle_freaker_')
        self.outfile = pjoin(self.tempdir, 'outfile.txt')
        self.input_handler = file_io.InputHandler(self.files,
                                                  self.dialect)
        self.output_handler = file_io.OutputHandler(self.outfile,
                                                    self.input_handler.dialect)


    def teardown_method(self, method):
        self.input_handler.close()
        self.output_handler.close()
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'FreakerTest'))


    def test_multicol(self):
        col_freak = mod.ColSetFreaker(self.input_handler,
                                      self.output_handler,
                                      self.col_type,
                                      self.number,
                                      self.sampling_method, self.sampling_rate,
                                      self.sortorder, self.sortcol,
                                      self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 1000
        assert len(col_freak.field_freq) == 8  # four A* * two B*
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']
            assert key[1] in ['B1', 'B2']

    def test_multicol_and_truncation(self):
        self.number = 4
        col_freak = mod.ColSetFreaker(self.input_handler,
                                      self.output_handler,
                                      self.col_type,
                                      self.number,
                                      self.sampling_method, self.sampling_rate,
                                      self.sortorder, self.sortcol,
                                      self.max_key_len)
        col_freak.build_freq(self.columns)
        assert col_freak.truncated
        assert len(col_freak.field_freq) == 4  # it's possible (but extremely unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']
            assert key[1] in ['B1', 'B2']

    def test_single_col(self):
        self.columns = [1]
        col_freak = mod.ColSetFreaker(self.input_handler,
                                      self.output_handler,
                                      self.col_type,
                                      self.number,
                                      self.sampling_method, self.sampling_rate,
                                      self.sortorder, self.sortcol,
                                      self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 1000
        assert len(col_freak.field_freq) == 4  # it's possible (but extremely unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']

    def test_interval_sampling(self):
        self.sampling_method = 'interval'
        self.sampling_rate = 10
        col_freak = mod.ColSetFreaker(self.input_handler,
                                      self.output_handler,
                                      self.col_type,
                                      self.number,
                                      self.sampling_method, self.sampling_rate,
                                      self.sortorder, self.sortcol,
                                      self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 100
        assert len(col_freak.field_freq) == 8  # it's possible (but unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']
            assert key[1] in ['B1', 'B2']



class TestCreateKey(object):

    def setup_method(self, method):
        (files, dialect, col_type, number, sampling_method, sampling_rate,
         _, max_key_len) = generate_col_freaker_dependencies()
        tempdir = tempfile.mkdtemp(prefix='test_gristle_freaker_')
        outfile = pjoin(tempdir, 'outfile.txt')
        sortorder = 'reverse'
        sortcol = 1
        input_handler = file_io.InputHandler(files,
                                             dialect)
        output_handler = file_io.OutputHandler(outfile,
                                               input_handler.dialect)
        self.col_freak = mod.ColSetFreaker(input_handler, output_handler, col_type,
                                           number, sampling_method, sampling_rate,
                                           sortorder, sortcol,
                                           max_key_len)

    def test_two_columns(self):
        fields = ['a', 'b', 'c', 'd', 'e', 'f']
        columns = [0, 2]
        key_tup = self.col_freak._create_key(fields, columns)
        assert key_tup == ('a', 'c')

    def test_one_column(self):
        fields = ['a', 'b', 'c', 'd', 'e', 'f']
        columns = [0]
        key_tup = self.col_freak._create_key(fields, columns)
        assert key_tup == ('a',)



class TestColumnLengthTracker(object):

    def setup_method(self, method):
        self.col_amount = 2
        self.col_len = mod.ColumnLengthTracker()

    def test_growing_length(self):
        # note: only tests a single column
        self.col_len.add_val(0, '1')
        assert self.col_len.max_dict[0] == 1
        self.col_len.add_val(0, '12')
        assert self.col_len.max_dict[0] == 2
        self.col_len.add_val(0, '123')
        assert self.col_len.max_dict[0] == 3

    def test_shrinking_length(self):
        # note: only tests a single column
        self.col_len.add_val(0, '123')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0, '123')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0, '1')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0, '')
        assert self.col_len.max_dict[0] == 3

    def test_empty_string(self):
        # note: only tests a single column
        self.col_len.add_val(0, '')
        assert self.col_len.max_dict[0] == 0

    def test_add_freq_list(self):
        # note: only tests a single column
        # dictionary key is a tuple, value is a count of occurances.  The value
        # doesn't actually matter for this test.
        freq = []

        self.col_len.add_all_values(freq)
        #this behavior changed when we changd the max_dict from a defaultdict to a dict
        #it now fails if there is nothing added
        #assert self.col_len.max_dict[0] == 0

        entry = (('a',), 0)
        freq.append(entry)
        entry = (('bb',), 0)
        freq.append(entry)
        entry = (('ccc',), 0)
        freq.append(entry)

        self.col_len.add_all_values(freq)
        assert self.col_len.max_dict[0] == 3

    def test_trunc_lengths(self):
        freq = []
        entry = (('a'*20, 'b'*10,), 0)
        freq.append(entry)
        self.col_len.add_all_values(freq)

        self.col_len.trunc_all_col_lengths(30)         # orig len
        assert self.col_len._get_tot_col_len() == 30   # orig len
        assert self.col_len.max_dict[0] == 20          # orig len
        assert self.col_len.max_dict[1] == 10          # orig len

        self.col_len.trunc_all_col_lengths(20)         # shorten by 10
        assert self.col_len._get_tot_col_len() == 20   # shorten by 10
        assert self.col_len.max_dict[0] == 10          # shorten by 10
        assert self.col_len.max_dict[1] == 10          # should be left untouched

        self.col_len.trunc_all_col_lengths(2)          # shorten by 28
        assert self.col_len._get_tot_col_len() == 2    # shorten by 28
        assert self.col_len.max_dict[0] == 1           # reduced evenly
        assert self.col_len.max_dict[1] == 1           # reduced evenly

        self.col_len.trunc_all_col_lengths(1)
        assert self.col_len._get_tot_col_len() == 1



def generate_col_freaker_dependencies():
    dialect = csv.Dialect
    dialect.delimiter = '|'
    dialect.quoting = csvhelper.get_quote_number('quote_minimal')
    dialect.quotechar = '"'
    dialect.has_header = False
    dialect.lineterminator = '\n'
    files = []
    files.append(generate_test_file(dialect.delimiter, 1000))
    columns = [1, 2]
    number = 1000
    col_type = 'specified'
    sampling_method = 'non'
    sampling_rate = None
    number = 4
    max_key_len = 50
    return files, dialect, col_type, number, sampling_method, sampling_rate, columns, max_key_len


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='FreakerTestIn_')
    fp = os.fdopen(fd, "w")

    for i in range(record_cnt):
        fields = []
        fields.append(str(i))
        fields.append(random.choice(('A1', 'A2', 'A3', 'A4')))
        fields.append(random.choice(('B1', 'B2')))
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn



