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
from os.path import dirname, basename, join as pjoin
import shutil
import sys
import tempfile

import envoy
import ruamel.yaml as yaml

import datagristle.csvhelper as csvhelper
import datagristle.test_tools as test_tools

EXAMPLE_DIR = pjoin(dirname(dirname(dirname(os.path.realpath(__file__)))), 'examples', 'gristle_profiler')
SCRIPT_DIR = dirname(dirname(os.path.realpath((__file__))))



class TestEmptyFile(object):
    """
       Supported:       quote_none, escaped delimiter
       Supported:       quote_all,  double-quote'd quote
       Not Supported:   quote_none, escaped newline

    """

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_profiler_')
        self.out_fqfn = pjoin(self.temp_dir, 'test_output.csv')
        self.cmd = None

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_empty_file(self):
        in_fqfn = pjoin(self.temp_dir, 'test_input.csv')
        with open(in_fqfn, 'w') as f:
            pass

        cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_profiler')}   \
                    -i {in_fqfn}
                    -o {self.out_fqfn}
              '''
        assert executor(cmd, expect_success=False) == 61



class TestSampleConfigs(object):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_profiler_')
        self.cmd = None

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_all_example_configs(self):
        test_count = 0
        for test_count, test_config_fn in enumerate(sorted(glob.glob(pjoin(EXAMPLE_DIR, '*example-*.yml')))):
            print('\n')
            print('=' * 100)
            print(test_config_fn)
            print('=' * 100)

            example_number = basename(test_config_fn).split('.')[0]

            self.load_config(example_number)
            self.make_command(example_number)
            print('\n**** Execution: ****')
            executor(self.cmd, expect_success=True)

            self.print_files()

            print('\n**** os diff of files: ****')
            assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0
            print('    test passed: actual file matched expected file')

        print('\n+++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(f'Tests run: {test_count}')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++')




    def load_config(self,
                    example_number):   # ex: 'example-1'

        self.config_fn = pjoin(EXAMPLE_DIR, f'{example_number}.yml')
        with open(self.config_fn) as buf:
            self.config = yaml.safe_load(buf)

        self.docstrings = []
        for rec in fileinput.input(self.config_fn):
            if rec.startswith('#'):
                self.docstrings.append(rec)
        fileinput.close()

        print(f'\n**** Config: ****')
        pp(self.config)

        print(f'\n**** Config docstring: ****')
        pp(self.docstrings)


    def make_command(self,
                     example_number):   # ex: 'example-1'

        self.config_fn = pjoin(EXAMPLE_DIR, f'{example_number}.yml')
        self.in_fqfn = glob.glob(pjoin(EXAMPLE_DIR, f'{example_number}_*_input.csv'))[0]
        self.expected_fqfn = glob.glob(pjoin(EXAMPLE_DIR, f'{example_number}_*_expectedout.csv'))[0]
        self.out_fqfn = pjoin(self.temp_dir, f'{example_number}_actualout.csv')

        self.cmd = f''' {pjoin(SCRIPT_DIR, 'gristle_profiler')}   \
                        -o {self.out_fqfn}
                        --verbosity debug
                        --config-fn {self.config_fn}
                    '''


    def print_files(self):

        print('\n**** command: ****')
        pp(self.cmd)

        print('\n**** input: ****')
        os.system(f'cat {self.in_fqfn}')

        print('\n**** actual: ****')
        os.system(f'cat {self.out_fqfn}')

        print('\n**** expected: ****')
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



