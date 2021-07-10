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

import glob
from pprint  import pprint as pp
import os
from os.path import dirname, basename, join as pjoin, isdir
import shutil
import tempfile

from colorama import Fore, Style, Back

import datagristle.test_tools as test_tools

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_differ')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestExamples(test_tools.TestExamples):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        super().setup_method(method)

        self.pgm = 'gristle_differ'
        self.example_dir = EXAMPLE_DIR
        self.script_dir = SCRIPT_DIR
        self.temp_dir = tempfile.mkdtemp(prefix=self.pgm)

        self.actual_dir = None
        self.expected_dir = None
        self.expected_files = []
        self.actual_files = []

    def test_example_01(self):
        self.run_example_config('example-01')

    def test_example_02(self):
        self.run_example_config('example-02')

    def test_example_03(self):
        self.run_example_config('example-03')

    def test_example_04(self):
        self.run_example_config('example-04')

    def test_example_05(self):
        self.run_example_config('example-05')

    def test_example_06(self):
        self.run_example_config('example-06')

    def test_example_07(self):
        self.run_example_config('example-07')

    def test_example_08(self):
        self.run_example_config('example-08')

    def test_example_09(self):
        self.run_example_config('example-09')

    #----------------------------------------------------------------------------
    # Test the diff features
    #----------------------------------------------------------------------------

    def test_example_21(self):
        self.run_example_config('example-21')

    def test_example_22(self):
        self.run_example_config('example-22')

    def test_example_23(self):
        self.run_example_config('example-23')

    def test_example_24(self):
        self.run_example_config('example-24')


    def run_example_config(self, example_number):
        test_config_fn = glob.glob(pjoin(self.example_dir, f'{example_number}.yml'))
        print('\n')
        print('=' * 100)
        print(test_config_fn)
        print('=' * 100)

        self.config_fn = pjoin(self.example_dir, f'{example_number}.yml')
        self.in_fqfn1 = glob.glob(pjoin(self.example_dir, f'{example_number}_*_input1.csv'))[0]
        self.in_fqfn2 = glob.glob(pjoin(self.example_dir, f'{example_number}_*_input2.csv'))[0]
        self.expected_files = glob.glob(pjoin(self.example_dir, f'{example_number}_output_files/*csv*'))

        self.load_config(example_number)
        self.actual_dir = self.config['out_dir']
        self.create_output_dir(self.actual_dir)
        self.make_command(example_number)
        print('\n**** Execution: ****')
        test_tools.executor(self.cmd, expect_success=True)

        self.actual_files = glob.glob(pjoin(self.config['out_dir'], f'{example_number}_*csv*'))
        self.print_files()

        print('\n**** os diff of files: ****')
        self.diff_file_pair(self.expected_files, self.actual_files, '.same')
        self.diff_file_pair(self.expected_files, self.actual_files, '.insert')
        self.diff_file_pair(self.expected_files, self.actual_files, '.delete')
        self.diff_file_pair(self.expected_files, self.actual_files, '.chgold')
        self.diff_file_pair(self.expected_files, self.actual_files, '.chgnew')


    def get_fqfn_of_filetype(self, fileset, filetype):
        """ Get the fully-qualified filename for a given type from a list
        """
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

        assert os.system(f'diff {sorted_expected_fqfn} {sorted_actual_fqfn}') == 0


    def create_output_dir(self,
                          out_dir):
        if not out_dir.startswith('/tmp/'):
            raise ValueError('Error: Output directory must be in /tmp')
        if isdir(out_dir):
            shutil.rmtree(out_dir)
        os.mkdir(out_dir)


    def make_command(self,
                     example_number):   # ex: 'example-1'
        self.cmd = f''' {pjoin(self.script_dir, self.pgm)}
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
            os.system(f'cat {fn}')

        print('\n**** expected: ****')
        for fn in self.expected_files:
            os.system(f'cat {fn}')


def get_file_type(filename):
    return filename.split('.')[-1]
