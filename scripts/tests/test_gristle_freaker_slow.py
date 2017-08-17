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
from pprint import pprint as pp

import datagristle.test_tools as test_tools
import datagristle.file_io as file_io

pgm_path = dirname(dirname(os.path.realpath((__file__))))
mod = test_tools.load_script(pjoin(pgm_path, 'gristle_freaker'))




class Test_build_freq(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'FreakerTest'))

    def test_multicol(self):

        dialect = csv.Dialect
        dialect.delimiter = '|'
        dialect.quoting = csv.QUOTE_MINIMAL
        dialect.quotechar = '"'
        dialect.has_header = False
        dialect.lineterminator = '\n'
        columns = [1, 2]
        files = []
        files.append(generate_test_file(dialect.delimiter, 10_000_000))
        (fd, outfile) = tempfile.mkstemp(prefix='FreakerTestOut_')
        input_handler = file_io.InputHandler(files,
                                             dialect.delimiter,
                                             dialect.quoting,
                                             dialect.quotechar,
                                             dialect.has_header)
        output_handler = file_io.OutputHandler(outfile,
                                               input_handler.dialect)

        col_freak = mod.ColSetFreaker(input_handler,
                                      output_handler,
                                      col_type='specified',
                                      number=20_000_000,
                                      sampling_method='non',
                                      sampling_rate=None,
                                      sort_order='reverse',
                                      sort_col=1,
                                      max_key_len=50)
        col_freak.build_freq(columns)
        assert not col_freak.truncated
        pp(col_freak.field_freq)
        assert sum(col_freak.field_freq.values()) == 10_000_000
        for key in col_freak.field_freq.keys():
            assert key[0] in ['A1', 'A2', 'A3', 'A4']
            assert key[1] in ['B1', 'B2']



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



