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
import fileinput
from pprint  import pprint as pp
import os
from os.path import basename, dirname, join as pjoin, isdir
import shutil
import tempfile
from typing import Optional

import ruamel.yaml as yaml

import datagristle.csvhelper as csvhelper
import datagristle.test_tools as test_tools

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_dir_merger')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestExamples:
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        self.pgm = 'gristle_dir_merger'
        self.example_dir = EXAMPLE_DIR
        self.script_dir = SCRIPT_DIR

        self.orig_temp_dir = tempfile.mkdtemp(prefix=self.pgm)
        shutil.copytree(self.example_dir, self.orig_temp_dir, dirs_exist_ok=True)
        self.temp_dir = tempfile.mkdtemp(prefix=self.pgm)
        shutil.copytree(self.example_dir, self.temp_dir, dirs_exist_ok=True)

        pp(os.listdir(self.temp_dir))

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_example_01_simple_directories(self):
        self.run_example_config('example-01')


    def test_example_02_nested_directories(self):
        self.run_example_config('example-02')



    def run_example_config(self, example_number, return_code=0):
        self.expected_fqfns = glob.glob(pjoin(self.orig_temp_dir, f'{example_number}*dest_results', '*'))


        test_config_fn = glob.glob(pjoin(self.temp_dir, f'{example_number}.yml'))
        print('\n')
        print('=' * 100)
        print(test_config_fn)
        print('=' * 100)

        self.load_config(example_number)
        self.make_command(example_number)

        print('\n**** Execution: ****')
        expected_success = True if return_code == 0 else False
        test_tools.executor(self.cmd, expect_success=expected_success)

        self.actual_fqfns = glob.glob(pjoin(self.temp_dir, f'{example_number}_*dest', '*'))
        self.print_files()

        expected_basenames = [basename(x) for x in self.expected_fqfns]
        actual_basenames = [basename(x) for x in self.actual_fqfns]
        assert expected_basenames == actual_basenames
        for fqfn in self.actual_fqfns:
            pp(f'{fqfn=}')
            assert self.get_file_contents(fqfn) in ('keep', 'same', 'dir', 'drop')



    def get_file_contents(self,
                          fqfn) -> Optional[str]:

        if isdir(fqfn):
            return 'dir'

        with open(fqfn, 'r') as inbuf:
            rec = inbuf.read()
            pp(rec)

        if 'drop' in rec:
            intention = 'drop'
        elif 'keep' in rec:
            intention = 'keep'
        elif 'same' in rec:
            intention = 'same'
        else:
            intention = 'unknown'

        return intention



    def load_config(self,
                    example_number):   # ex: 'example-1'

        self.config_fn = pjoin(self.temp_dir, f'{example_number}.yml')


    def make_command(self,
                     example_number):   # ex: 'example-1'

        self.cmd = f''' {pjoin(self.script_dir, self.pgm)}   \
                        --verbosity debug
                        --config-fn {self.config_fn}
                    '''


    def print_files(self):

        pp('')
        pp('*** EXPECTED FQFNs ***')
        pp(self.expected_fqfns)

        pp('')
        pp('*** ACTUAL FQFNs ***')
        pp(self.actual_fqfns)

