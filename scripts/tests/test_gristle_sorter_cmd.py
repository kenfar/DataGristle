#zR!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2020 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

import csv
from pprint  import pprint as pp
import os
from os.path import dirname
from os.path import join as pjoin
import shutil
import tempfile

import envoy

import datagristle.csvhelper as csvhelper

SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))
DATA_DIR = pjoin(dirname(SCRIPT_DIR), 'data')




class TestKeyOptions(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_sorter_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_one_key(self):
        in_fqfn = create_test_file(self.temp_dir, header=False)
        dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=False, doublequote=False)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
                    -q quote_none -d ',' --has-no-header --no-doublequote
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn, dialect)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '4'

    def test_two_keys(self):
        in_fqfn = create_complex_test_file(self.temp_dir, header=False)
        dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=False, doublequote=False)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0ir 1sf
                    -q quote_none -d ',' --has-no-header --no-doublequote
              '''
        executor(cmd, expect_success=True)
        actual_recs = get_file_contents(out_fqfn, dialect)
        expected_recs = [['4', 'aaa', 'a23'],
                         ['4', 'aba', 'a23'],
                         ['4', 'bbb', 'a23'],
                         ['3', 'aaa', 'b23'],
                         ['3', 'aaa', 'b23'],
                         ['1', 'aaa', 'a23']]
        pp(actual_recs)
        assert actual_recs == expected_recs



class TestDuplicateOptions(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_sorter_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_nondup(self):
        in_fqfn = create_test_file(self.temp_dir, duplicate=True)
        dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=False, doublequote=False)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn, dialect)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '3'
        assert recs[4][0] == '4'


    def test_dup(self):
        in_fqfn = create_test_file(self.temp_dir, duplicate=True, header=False)
        dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=False, doublequote=False)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
                    -D
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn, dialect)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '4'



class TestFileContents(object):
    """
       Supported:       quote_none, escaped delimiter
       Supported:       quote_all,  double-quote'd quote
       Not Supported:   quote_none, escaped newline

    """

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_sorter_')
        self.out_fqfn = pjoin(self.temp_dir, 'testfile.csv.sorted')
        self.cmd = None

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_empty_file(self):

        in_fqfn = pjoin(self.temp_dir, 'testfile.csv')
        with open(in_fqfn, 'w') as f:
            pass

        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
              '''
        assert executor(cmd, expect_success=False) == 61


    def test_quotenone_escaped_quote(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=True, escapechar='\\')

        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quotenone_escaped_quote.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quotenone_escaped_quote.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quotenone_escaped_delimiter(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, quotechar=None, has_header=True,
                                         escapechar='\\', doublequote=False)

        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quotenone_escaped_delimiter.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quotenone_escaped_delimiter.csv.sorted')

        self.make_command()
        pp(self.cmd)
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_escaped_delimiter(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=False, escapechar='\\')

        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_delimiter.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_delimiter.csv.sorted')

        self.make_command()
        print(self.cmd)
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_escaped_newline(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=False, escapechar='\\')
        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_newline.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_newline.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_escaped_quote(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=False, escapechar='\\')
        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_quote.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_escaped_quote.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_doublequote_quote(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=True)
        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_quote.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_quote.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_doublequote_delimiter(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=True)
        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_delimiter.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_delimiter.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def test_quoteall_doublequote_newline(self):

        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_ALL, quotechar='"', has_header=True, doublequote=True)
        self.in_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_newline.csv')
        self.expected_fqfn = pjoin(DATA_DIR, 'dialect_quoteall_doublequote_newline.csv.sorted')

        self.make_command()
        executor(self.cmd, expect_success=True)

        self.load_files()
        self.print_files()

        assert self.out_recs == self.expected_recs
        print('os diff of files: ')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0





    def make_command(self):
        assert not (self.dialect.doublequote and self.dialect.escapechar)
        doublequote_str = '--doublequote' if self.dialect.doublequote else '--no-doublequote'
        escapechar_str  = f"--escapechar '{self.dialect.escapechar}'" if self.dialect.escapechar else ''
        self.cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                        -i {self.in_fqfn}
                        -o {self.out_fqfn}
                        -k 1sf
                        --quoting {csvhelper.get_quote_name(self.dialect.quoting).lower()}
                        --delimiter '{self.dialect.delimiter}'
                        --has-header
                        --verbosity debug
                        {doublequote_str}
                        {escapechar_str}
                    '''
        pp(self.cmd)


    def load_files(self):

        self.in_recs = get_file_contents(self.in_fqfn, self.dialect)
        self.out_recs = get_file_contents(self.out_fqfn, self.dialect)
        self.expected_recs = get_file_contents(self.expected_fqfn, self.dialect)


    def print_files(self):

        print('\n command: ')
        pp(self.cmd)

        print('\n input: ')
        self.in_recs = get_file_contents(self.in_fqfn, self.dialect)
        pp(self.in_recs)
        os.system(f'cat {self.in_fqfn}')

        print('\n actual: ')
        self.out_recs = get_file_contents(self.out_fqfn, self.dialect)
        pp(self.out_recs)
        os.system(f'cat {self.out_fqfn}')

        print('\n expected: ')
        self.expected_recs = get_file_contents(self.expected_fqfn, self.dialect)
        pp(self.expected_recs)
        os.system(f'cat {self.expected_fqfn}')



def executor(cmd, expect_success=True):
    runner = envoy.run(cmd)
    status_code = runner.status_code
    print(runner.std_out)
    print(runner.std_err)
    if expect_success:
        assert status_code == 0
    else:
        assert status_code != 0
    return status_code


def get_file_contents(fqfn, dialect):
    recs = []
    with open(fqfn, newline='') as buf:
       reader = csv.reader(buf, dialect=dialect)
       recs = list(reader)
    return recs


def create_test_file(temp_dir, delimiter=',', duplicate=False, header=False):
    fqfn = pjoin(temp_dir, 'testfile.csv')
    with open(fqfn, 'w') as f:
        if header:
            f.write(delimiter.join(['num', 'alpha', 'alphanumeric']) + '\n')
        f.write(delimiter.join(['4', 'aaa', 'a23']) + '\n')
        f.write(delimiter.join(['2', 'bbb', 'a23']) + '\n')
        f.write(delimiter.join(['1', 'bbb', 'b23']) + '\n')
        f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
        if duplicate:
            f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
    return fqfn


def create_complex_test_file(temp_dir, delimiter=',', duplicate=False, header=False):
    """ Has a few more features;
        - num 4 rows are unique based on num + alpha column
    - num 1 rows are unique based on num column only
    - num 3 rows are total duplicates
    """
    fqfn = pjoin(temp_dir, 'testfile.csv')
    with open(fqfn, 'w') as f:
        if header:
            f.write(delimiter.join(['num', 'alpha', 'alphanumeric']) + '\n')
        f.write(delimiter.join(['4', 'aaa', 'a23']) + '\n')
        f.write(delimiter.join(['4', 'bbb', 'a23']) + '\n')
        f.write(delimiter.join(['4', 'aba', 'a23']) + '\n')
        f.write(delimiter.join(['1', 'aaa', 'a23']) + '\n')
        f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
        f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
    return fqfn

