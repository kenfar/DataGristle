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



    def test_all_example_configs(self):
        for test_count, test_config_fn in enumerate(sorted(glob.glob(pjoin(self.example_dir, '*example-*.yml')))):
            print('\n')
            print('=' * 100)
            print(test_config_fn)
            print('=' * 100)

            example_number = basename(test_config_fn).split('.')[0]
            self.config_fn = pjoin(self.example_dir, f'{example_number}.yml')
            self.in_fqfn1 = glob.glob(pjoin(self.example_dir, f'{example_number}_*_input1.csv'))[0]
            self.in_fqfn2 = glob.glob(pjoin(self.example_dir, f'{example_number}_*_input2.csv'))[0]
            self.expected_files = glob.glob(pjoin(self.example_dir, f'{example_number}_expected_output_files/*csv*'))

            self.load_config(example_number)
            self.actual_dir = self.config['out-dir']
            self.create_output_dir(self.actual_dir)
            self.make_command(example_number)
            print('\n**** Execution: ****')
            test_tools.executor(self.cmd, expect_success=True)

            self.actual_files = glob.glob(pjoin(self.config['out-dir'], f'{example_number}_*csv*'))
            self.print_files()

            print('\n**** os diff of files: ****')

            rc = self.diff_file_pair(self.expected_files, self.actual_files, '.same')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.insert')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.delete')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.chgold')
            rc += self.diff_file_pair(self.expected_files, self.actual_files, '.chgnew')

            if rc == 0:
                print(Fore.GREEN + '\nTEST PASSED: actual files matched expected files')
            else:
                print(Fore.RED + '\nTEST FAILED: file differences were encountered!')
            print(Fore.RESET)

        print('\n+++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(f'Tests run: {test_count}')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++')


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

        return os.system(f'diff {sorted_expected_fqfn} {sorted_actual_fqfn}')


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


