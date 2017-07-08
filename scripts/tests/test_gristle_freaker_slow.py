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

import tempfile
import random
import csv
import os
from os.path import dirname, join as pjoin

import datagristle.test_tools as test_tools

pgm_path = dirname(dirname(os.path.realpath((__file__))))
mod = test_tools.load_script(pjoin(pgm_path, 'gristle_freaker'))


RECORD_NUMBER = 1000000   # 1 Million




class Test_build_freq(object):

    def setup_method(self, method):
        self.dialect = csv.Dialect
        self.dialect.delimiter = '|'
        self.dialect.quoting = csv.QUOTE_MINIMAL
        self.dialect.quotechar = '"'
        self.dialect.has_header = False
        self.dialect.lineterminator = '\n'
        self.files = []
        self.files.append(generate_test_file(self.dialect.delimiter, RECORD_NUMBER))
        self.columns = [1, 2]
        self.number = RECORD_NUMBER

    def teardown_method(self, method):
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'FreakerTest'))

    def test_multicol(self):
        col_type = 'specified'
        sampling_method = 'non'
        sampling_rate = None
        sortorder = 'reverse'
        sortcol = 1
        maxkeylen = 50
        col_freak = mod.ColFreaker(self.files, self.dialect, col_type,
                                   self.number,
                                   sampling_method, sampling_rate,
                                   sortorder, sortcol, maxkeylen)
        col_freak.build_freq(self.columns)
        assert not col_freak.truncated
        assert sum(col_freak.field_freq.values()) == RECORD_NUMBER
        assert len(col_freak.field_freq) == 8
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']
            assert key[1] in ['B1', 'B2']



def generate_col_freaker_dependencies():
    dialect = csv.Dialect
    dialect.delimiter = '|'
    dialect.quoting = csv.QUOTE_MINIMAL
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
    return files, dialect, col_type, number, sampling_method, sampling_rate, columns


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



