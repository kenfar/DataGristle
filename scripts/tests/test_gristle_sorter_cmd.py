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

import tempfile
import shutil
import csv
from pprint  import pprint as pp
import os
from os.path import dirname
from os.path import join as pjoin

import envoy

import datagristle.csvhelper as csvhelper

SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestKeyOptions(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_sorter_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_one_key(self):
        in_fqfn = create_test_file(self.temp_dir)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '4'

    def test_two_keys(self):
        in_fqfn = create_complex_test_file(self.temp_dir)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0ir 1sf
              '''
        executor(cmd, expect_success=True)
        actual_recs = get_file_contents(out_fqfn)
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
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '3'
        assert recs[4][0] == '4'


    def test_dup(self):
        in_fqfn = create_test_file(self.temp_dir, duplicate=True)
        out_fqfn = in_fqfn + '.sorted'
        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_sorter')}   \
                    -i {in_fqfn}
                    -o {out_fqfn}
                    -k 0sf
                    -D
              '''
        executor(cmd, expect_success=True)
        recs = get_file_contents(out_fqfn)
        assert recs[0][0] == '1'
        assert recs[1][0] == '2'
        assert recs[2][0] == '3'
        assert recs[3][0] == '4'





def executor(cmd, expect_success=True):
    runner = envoy.run(cmd)
    print(runner.std_out)
    print(runner.std_err)
    if expect_success:
        assert runner.status_code == 0
    else:
        assert runner.status_code != 0



def get_file_contents(fqfn):
    recs = []
    with open(fqfn, newline='') as buf:
       reader = csv.reader(buf)
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

