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
from pprint import pprint as pp
from os.path import dirname, join as pjoin

sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))
import datagristle.test_tools as test_tools
pgm_path = dirname(dirname(os.path.realpath((__file__))))
mod = test_tools.load_script(pjoin(pgm_path, 'gristle_freaker'))


# Taken out because I actually want those prints sometimes, plus it
# won't work with wb on python3 anyhow
# shut off the printing of warnings & info statements from module
#old_stdout = sys.stdout
#old_stderr = sys.stderr
#null       = open(os.devnull, 'wb')
#sys.stdout = sys.stderr = null


def generate_col_freaker_dependencies():
    dialect                = csv.Dialect
    dialect.delimiter      = '|'
    dialect.quoting        = True
    dialect.quotechar      = '"'
    dialect.has_header     = False
    dialect.lineterminator = '\n'
    files                  = []
    files.append(generate_test_file(dialect.delimiter, 1000))
    columns                = [1, 2]
    number                 = 1000
    col_type               = 'specified'
    sampling_method        = 'non'
    sampling_rate          = None
    number                 = 4
    max_key_len            = 50
    return files, dialect, col_type, number, sampling_method, sampling_rate, columns, max_key_len


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='FreakerTestIn_')
    fp = os.fdopen(fd,"w")

    for i in range(record_cnt):
        fields = []
        fields.append(str(i))
        fields.append(random.choice(('A1','A2','A3','A4')))
        fields.append(random.choice(('B1','B2')))
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn



class Test_build_freq(object):

    def setup_method(self, method):
        self.dialect                = csv.Dialect
        self.dialect.delimiter      = '|'
        self.dialect.quoting        = csv.QUOTE_MINIMAL
        self.dialect.quotechar      = '"'
        self.dialect.has_header     = False
        self.dialect.lineterminator = '\n'
        self.files                  = []
        self.files.append(generate_test_file(self.dialect.delimiter, 1000))
        self.columns                = [1, 2]
        self.col_type               = 'specified'
        self.number                 = 1000
        self.sampling_method        = 'non'
        self.sampling_rate          = None
        self.sortorder              = 'reverse'
        self.sortcol                = 1
        self.max_key_len            = 50

    def teardown_method(self, method):
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'FreakerTest'))

    def test_bf_01_multicol(self):
        col_freak = mod.ColFreaker(self.files, self.dialect, self.col_type,
                                   self.number,
                                   self.sampling_method, self.sampling_rate,
                                   self.sortorder, self.sortcol,
                                   self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 1000
        assert len(col_freak.field_freq) == 8  # four A* * two B*
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1','A2','A3','A4']
            assert key[1] in ['B1','B2']

    def test_bf_02_multicol_and_truncation(self):
        self.number     = 4
        col_freak = mod.ColFreaker(self.files, self.dialect, self.col_type,
                                   self.number,
                                   self.sampling_method, self.sampling_rate,
                                   self.sortorder, self.sortcol,
                                   self.max_key_len)
        col_freak.build_freq(self.columns)
        assert col_freak.truncated
        assert len(col_freak.field_freq) == 4  # it's possible (but extremely unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1','A2','A3','A4']
            assert key[1] in ['B1','B2']

    def test_bf_03_single_col(self):
        self.columns    = [1]
        col_freak = mod.ColFreaker(self.files, self.dialect, self.col_type,
                                   self.number,
                                   self.sampling_method, self.sampling_rate,
                                   self.sortorder, self.sortcol,
                                   self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 1000
        assert len(col_freak.field_freq) == 4  # it's possible (but extremely unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1','A2','A3','A4']

    def test_bf_03_interval_sampling(self):
        self.sampling_method = 'interval'
        self.sampling_rate   = 10
        col_freak = mod.ColFreaker(self.files, self.dialect, self.col_type,
                                   self.number,
                                   self.sampling_method, self.sampling_rate,
                                   self.sortorder, self.sortcol,
                                   self.max_key_len)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == 100
        assert len(col_freak.field_freq) == 8  # it's possible (but unlikely) that there could be fewer entries
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1','A2','A3','A4']
            assert key[1] in ['B1','B2']



class Test_get_opts_and_args(object):

    def test_goaa_happy_path(self):
        sys.argv = ['../gristle_freaker', 'census.csv', '-c', '1']
        cmd_parser = mod.CommandLineParser()
        opts       = cmd_parser.opts
        files      = cmd_parser.files
        assert opts.columns    == [1]
        assert opts.output     == '-'
        assert opts.writelimit == 0
        assert opts.recdelimiter is None
        assert opts.delimiter    is None
        assert opts.quoting      is False
        assert opts.hasheader    is None
        assert opts.sampling_method == 'non'
        assert opts.sampling_rate   is None
        assert opts.sortcol    == 1
        assert opts.sortorder  == 'reverse'

    def test_goaa_check_invalid_columns(self):
        sys.argv = ['../gristle_freaker', 'census.csv', '-c', 'd']
        try:
            cmd_parser = mod.CommandLineParser()
            opts       = cmd_parser.opts
            files      = cmd_parser.files
        except SystemExit:
            pass
        except e:
            pytest.fail('unexpected exception thrown: ', e)
        else:
            pytest.fail('expected exception not thrown')

    def test_goaa_check_invalid_maxkenlen(self):
        sys.argv = ['../gristle_freaker', 'census.csv', '--maxkeylen', 'blah']
        try:
            cmd_parser = mod.CommandLineParser()
            opts       = cmd_parser.opts
            files      = cmd_parser.files
        except SystemExit:
            pass
        except e:
            pytest.fail('unexpected exception thrown: ', e)
        else:
            pytest.fail('expected exception not thrown')

    def test_goaa_check_valid_maxkenlen(self):
        sys.argv = ['../gristle_freaker', 'census.csv', '-c', '0', '--maxkeylen', '50']

        try:
            cmd_parser = mod.CommandLineParser()
            opts       = cmd_parser.opts
            files      = cmd_parser.files
            if opts.maxkeylen != 50:
                pytest.fail('maxkeylen results did not match expected values: ')
        except SystemExit:
            pytest.fail('Unexpected exception thrown')
        except:
            e = sys.exc_info()[1]
            pytest.fail('Unexpected exception thrown: %s' % e)
            raise


class Test_dict_sorter(object):

    def setup_method(self, method):
        self.dialect                = csv.Dialect
        self.dialect.delimiter      = '|'
        self.dialect.quoting        = True
        self.dialect.quotechar      = '"'
        self.dialect.has_header     = False
        self.dialect.lineterminator = '\n'
        self.files                  = []
        self.files.append(generate_test_file(self.dialect.delimiter, 1))
        self.columns                = [1, 2]
        self.col_type               = 'specified'
        self.number                 = 1000
        self.sampling_method        = 'non'
        self.sampling_rate          = None
        self.sortorder              = 'reverse'
        self.sortcol                = 1
        self.max_key_len            = 50
        self.col_freak = mod.ColFreaker(self.files, self.dialect, self.col_type,
                                   self.number,
                                   self.sampling_method, self.sampling_rate,
                                   self.sortorder, self.sortcol,
                                   self.max_key_len)

    def test_fs_01_multi_key(self):
        field_freq = {}
        field_freq[('a1', 'a2', 'a3')] = 2
        field_freq[('k1', 'k2', 'k3')] = 3
        field_freq[('c1', 'c2', 'c3')] = 4
        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=1, revorder=True)
        assert out_freq[0][1] == 4

        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=1, revorder=False)
        assert out_freq[0][1] == 2

        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=0, revorder=True)
        assert out_freq[0][1] == 3

        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=0, revorder=False)
        assert out_freq[0][1] == 2

    def test_fs_02_single_key(self):
        field_freq = {}
        field_freq[('a1',)] = 2
        field_freq[('k1',)] = 3
        field_freq[('c1',)] = 4
        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=1, revorder=True)
        assert out_freq[0][1] == 4

    def test_fs_03_empty_file(self):
        field_freq = {}
        out_freq = self.col_freak._dict_sorter(field_freq, sortcol=1, revorder=True)
        assert out_freq == []



class Test_create_output_row(object):

    def setup_method(self, method):
        self.in1   = 'aaa1'
        self.in2   = 'aaa2'
        self.in3   = 'aaa3'
        self.count = 5
        self.freq_tup = ((self.in1, self.in2, self.in3), self.count)
        self.col_len  = mod.ColumnLengthTracker()
        self.col_len.add_val(0, self.in1)
        self.col_len.add_val(1, self.in2)
        self.col_len.add_val(2, self.in3)
        self.key_label = ''

    def test_cor_01_parts(self):

        self.out_row = mod.create_output_row(self.freq_tup,
                                             self.col_len,
                                             self.key_label)
        parts   = self.out_row[:-1].split('-')
        assert self.in1 == parts[0].strip()
        assert self.in2 == parts[1].strip()
        assert self.in3 == parts[2].strip()
        assert self.count == int(parts[3])

    def test_cor_02_lengths(self):

        self.out_row = mod.create_output_row(self.freq_tup,
                                             self.col_len,
                                             self.key_label)
        parts   = self.out_row[:-1].split('-')
        assert len(parts[0]) == len(self.in1) + 3
        assert len(parts[1]) == len(self.in2) + 4
        assert len(parts[2]) == len(self.in3) + 4
        assert len(parts[3]) == len(str(self.count)) + 2

    def test_cor_03_trunc_lengths(self):

        self.col_len.trunc_all_col_lengths(3)
        self.out_row = mod.create_output_row(self.freq_tup,
                                             self.col_len,
                                             self.key_label)
        parts   = self.out_row[:-1].split('-')
        assert len(parts[0]) == 1 + 3
        assert len(parts[1]) == 1 + 4
        assert len(parts[2]) == 1 + 4
        assert len(parts[3]) == len(str(self.count)) + 2





class Test_create_key(object):

    def setup_method(self, method):
        (files, dialect, col_type, number, sampling_method, sampling_rate,
         columns, max_key_len) = generate_col_freaker_dependencies()
        sortorder              = 'reverse'
        sortcol                = 1

        self.col_freak = mod.ColFreaker(files, dialect, col_type,
                                        number, sampling_method, sampling_rate,
                                        sortorder, sortcol,
                                        max_key_len)

    def test_fs_01_multi_key(self):
        field_freq = {}

    def test_ck_01(self):
        fields  = ['a', 'b', 'c', 'd', 'e', 'f']
        columns = [0, 2]
        key_tup = self.col_freak._create_key(fields, columns)
        assert key_tup == ('a','c')

    def test_ck_02(self):
        fields  = ['a', 'b', 'c', 'd', 'e', 'f']
        columns = [0]
        key_tup = self.col_freak._create_key(fields, columns)
        assert key_tup == ('a',)





class Test_ColumnLengthTracker(object):

    def setup_method(self, method):
        self.col_amount = 2
        self.col_len = mod.ColumnLengthTracker()

    def test_clt_01_growing_length(self):
        # note: only tests a single column
        self.col_len.add_val(0,'1')
        assert self.col_len.max_dict[0] == 1
        self.col_len.add_val(0,'12')
        assert self.col_len.max_dict[0] == 2
        self.col_len.add_val(0,'123')
        assert self.col_len.max_dict[0] == 3

    def test_clt_02_shrinking_length(self):
        # note: only tests a single column
        self.col_len.add_val(0,'123')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0,'123')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0,'1')
        assert self.col_len.max_dict[0] == 3
        self.col_len.add_val(0,'')
        assert self.col_len.max_dict[0] == 3

    def test_clt_03_empty_string(self):
        # note: only tests a single column
        self.col_len.add_val(0,'')
        assert self.col_len.max_dict[0] == 0

    def test_clt_04_add_freq_list(self):
        # note: only tests a single column
        # dictionary key is a tuple, value is a count of occurances.  The value
        # doesn't actually matter for this test.
        freq = []

        self.col_len.add_all_values(freq)
        assert self.col_len.max_dict[0] == 0

        entry = (('a',),0)
        freq.append(entry)
        entry = (('bb',),0)
        freq.append(entry)
        entry = (('ccc',),0)
        freq.append(entry)

        self.col_len.add_all_values(freq)
        assert self.col_len.max_dict[0] == 3

    def test_clt_05_trunc_lengths(self):
        freq = []
        entry = (('a'*20,'b'*10,), 0)
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


class Test_ColumnLengthTracker_2col(Test_ColumnLengthTracker):
    """ Not implemented yet
    """

    def setup_method(self, method):
        self.col_amount = 2
        self.col_len = mod.ColumnLengthTracker()


class Test_ColumnLengthTracker_1col(Test_ColumnLengthTracker):
    """ Not implemented yet
    """

    def setup_method(self, method):
        self.col_amount = 1
        self.col_len = mod.ColumnLengthTracker()

