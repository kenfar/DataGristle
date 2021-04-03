#zR!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2020-2021 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

import csv
import fileinput
import glob
from pprint  import pprint as pp
import os
from os.path import dirname, basename, join as pjoin, isdir
import shutil
import sys
import tempfile

import envoy
import ruamel.yaml as yaml

import datagristle.csvhelper as csvhelper

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_differ')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestSampleConfigs(object):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_differ_')
        self.cmd = None
        self.actual_dir = None
        self.expected_dir = None
        self.expected_files = []
        self.actual_files = []

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)
        pass

    def test_all_example_configs(self):
        for test_count, test_config_fn in enumerate(sorted(glob.glob(pjoin(EXAMPLE_DIR, '*example-*.yml')))):
            print('\n')
            print('=' * 100)
            print(test_config_fn)
            print('=' * 100)

            example_number = basename(test_config_fn).split('.')[0]
            self.config_fn = pjoin(EXAMPLE_DIR, f'{example_number}.yml')
            self.in_fqfn1 = glob.glob(pjoin(EXAMPLE_DIR, f'{example_number}_*_input1.csv'))[0]
            self.in_fqfn2 = glob.glob(pjoin(EXAMPLE_DIR, f'{example_number}_*_input2.csv'))[0]
            self.expected_files = glob.glob(pjoin(EXAMPLE_DIR, f'{example_number}_expected_output_files/*csv*'))

            self.load_config(example_number)
            self.create_output_dir(self.actual_dir)
            self.make_command(example_number)
            print('\n**** Execution: ****')
            executor(self.cmd, expect_success=True)

            self.actual_files = glob.glob(pjoin(self.config['out-dir'], f'{example_number}_*csv*'))
            self.print_files()

            print('\n**** os diff of files: ****')

            rc = self.diff_file_pair(self.expected_files, self.actual_files, '.same')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.insert')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.delete')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.chgold')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.chgnew')

            if rc == 0:
                print('\ntest passed: actual files matched expected files')
            else:
                print('\ntest FAILED: file differences were encountered!')

        print('\n+++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(f'Tests run: {test_count}')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++')


    def get_fqfn_of_filetype(self, fileset, filetype):
        return [fqfn for fqfn in fileset if fqfn.endswith(filetype)][0]


    def diff_file_pair(self, expected_files, actual_files, filetype):
        expected_fqfn = self.get_fqfn_of_filetype(expected_files, filetype)
        print(f"\nFor filetype: {expected_fqfn.split('.')[-1]} ")

        actual_fqfn = self.get_fqfn_of_filetype(actual_files, filetype)

        print('')
        print(f'\n     Expected fqfn (simple unix-sorted) - {expected_fqfn}: ')
        sorted_expected_fqfn = pjoin(self.temp_dir, basename(expected_fqfn)) + '.expected'
        os.system(f'sort {expected_fqfn} > {sorted_expected_fqfn}')
        os.system(f'cat {sorted_expected_fqfn}')

        print(f'\n     Actual fqfn (simple unix-sorted) - {actual_fqfn}: ')
        sorted_actual_fqfn = pjoin(self.temp_dir, basename(actual_fqfn)) + '.actual'
        os.system(f'sort {actual_fqfn} > {sorted_actual_fqfn}')
        os.system(f'cat {sorted_actual_fqfn}')

        rc = os.system(f'diff {sorted_expected_fqfn} {sorted_actual_fqfn}')
        return rc


    def load_config(self,
                    example_number):   # ex: 'example-1'

        self.config_fn = pjoin(EXAMPLE_DIR, f'{example_number}.yml')
        with open(self.config_fn) as buf:
            self.config = yaml.safe_load(buf)

        self.actual_dir = self.config['out-dir']
        self.docstrings = []
        for rec in fileinput.input(self.config_fn):
            if rec.startswith('#'):
                self.docstrings.append(rec)
        fileinput.close()

        print(f'\n**** Config: ****')
        pp(self.config)

        print(f'\n**** Config docstring: ****')
        pp(self.docstrings)


    def create_output_dir(self,
                          out_dir):
        if not out_dir.startswith('/tmp/'):
            raise ValueError('Error: Output directory must be in /tmp')

        if isdir(out_dir):
            shutil.rmtree(out_dir)

        os.mkdir(out_dir)



    def make_command(self,
                     example_number):   # ex: 'example-1'

        self.cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_differ')}
                        --verbosity debug
                        --config-fn {self.config_fn}
                    '''


    def print_files(self):

        print('\n**** command: ****')
        pp(self.cmd)

        print('\n**** input1: ****')
        os.system(f'cat {self.in_fqfn1}')

        print('\n**** input2: ****')
        os.system(f'cat {self.in_fqfn2}')

        print('\n**** actual: ****')
        for fn in self.actual_files:
            #print(f'{get_file_type(fn)}: ', end='')
            os.system(f'cat {fn}')

        print('\n**** expected: ****')
        for fn in self.expected_files:
            os.system(f'cat {fn}')


def get_file_type(filename):
    return filename.split('.')[-1]


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



