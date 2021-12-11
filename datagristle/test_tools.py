#!/usr/bin/env python
""" Provides tools to assist in testing.
"""
import csv
import fileinput
import glob
import importlib
import importlib.machinery
import importlib.util
import os
from os.path import basename, join as pjoin
from pprint import pprint as pp
import random
import shutil
import sys
import tempfile
import types

from colorama import Fore, Style, Back
import envoy
import ruamel.yaml as yaml

sys.dont_write_bytecode = True


def load_script(script_name: str):
    """ Loads a script in the parent directory as a module, and passes back
        the module reference.  This is used when there is no .py suffix.

        Inputs:  the name of the script, without a directory
        Outputs: the module reference
    """
    test_dir = os.path.dirname(os.path.realpath(__file__))
    script_dir = os.path.dirname(test_dir)
    script_filepath = os.path.join(script_dir, script_name)

    # A number of solutions offered for this don't work - since they don't 
    # populate the __file__ attribute in the module.  This does:
    importlib.machinery.SOURCE_SUFFIXES.append('') # empty string to allow any file
    spec = importlib.util.spec_from_file_location(script_name, script_filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return mod


def get_app_root() -> str:
    """ returns the application root directory
    """
    test_dir = os.path.dirname(os.path.realpath(__file__))
    script_dir = os.path.dirname(test_dir)
    app_dir = os.path.dirname(script_dir)
    return app_dir


def print_whoami():
    name = sys._getframe(1).f_code.co_name
    file = sys._getframe(1).f_code.co_filename
    line = sys._getframe(1).f_lineno
    print('Function: %s in file: %s at line: %d' % (name, file, line))



def temp_file_remover(fqfn_prefix: str) -> None:
    for temp_file in glob.glob('%s*' % fqfn_prefix):
        os.remove(temp_file)


def generate_7x7_test_file(prefix: str, hasheader: bool = False, delimiter: str = '|', dirname: str = None):
    dlm = delimiter
    data_7x7 = []
    if hasheader:
        data_7x7.append(f'col0{dlm}scol1{dlm}scol2{dlm}scol3{dlm}scol4{dlm}scol5{dlm}scol6')

    data_7x7.append(f'0-0{dlm}0-1{dlm}0-2{dlm}0-3{dlm}0-4{dlm}0-5{dlm}0-6')
    data_7x7.append(f'1-0{dlm}1-1{dlm}1-2{dlm}1-3{dlm}1-4{dlm}1-5{dlm}1-6')
    data_7x7.append(f'2-0{dlm}2-1{dlm}2-2{dlm}2-3{dlm}2-4{dlm}2-5{dlm}2-6')
    data_7x7.append(f'3-0{dlm}3-1{dlm}3-2{dlm}3-3{dlm}3-4{dlm}3-5{dlm}3-6')
    data_7x7.append(f'4-0{dlm}4-1{dlm}4-2{dlm}4-3{dlm}4-4{dlm}4-5{dlm}4-6')
    data_7x7.append(f'5-0{dlm}5-1{dlm}5-2{dlm}5-3{dlm}5-4{dlm}5-5{dlm}5-6')
    data_7x7.append(f'6-0{dlm}6-1{dlm}6-2{dlm}6-3{dlm}6-4{dlm}6-5{dlm}6-6')

    if dirname:
        (fd, fqfn) = tempfile.mkstemp(prefix=prefix, dir=dirname)
    else:
        (fd, fqfn) = tempfile.mkstemp(prefix=prefix)

    fp = os.fdopen(fd,"w")
    for rec in data_7x7:
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn, data_7x7


def touch(fname: str, times=None) -> None:
    with open(fname, 'a'):
        os.utime(fname, times)




class TestExamples(object):
    """ Test all configs and files in the example directory for this program
    """

    def setup_method(self, method):
        self.pgm = None
        self.script_dir = None
        self.example_dir = ''
        self.temp_dir = tempfile.mkdtemp(prefix=self.pgm)
        self.cmd = None

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def run_example_config(self, example_number, return_code=0):
        test_config_fn = glob.glob(pjoin(self.example_dir, f'{example_number}.yml'))
        print('\n')
        print('=' * 100)
        print(test_config_fn)
        print('=' * 100)

        self.load_config(example_number)
        self.make_command(example_number)
        print('\n**** Execution: ****')
        pp(self.cmd)
        expected_success = True if return_code == 0 else False
        executor(self.cmd, expect_success=expected_success)

        self.print_files()

        print('\n**** os diff of files: ****')
        pp(f'expected_fqfn={self.expected_fqfn}')
        pp(f'actual_fqfn={self.out_fqfn}')
        assert os.system(f'diff {self.out_fqfn} {self.expected_fqfn}') == 0


    def run_example_config_for_return_code(self, example_number, return_code=0):
        test_config_fn = glob.glob(pjoin(self.example_dir, f'{example_number}.yml'))
        print('\n')
        print('=' * 100)
        print(test_config_fn)
        print('=' * 100)

        self.load_config(example_number)
        self.make_command(example_number)
        print('\n**** Execution: ****')
        pp(self.cmd)
        expected_success = True if return_code == 0 else False
        executor(self.cmd, expect_success=expected_success)

        self.print_files()

        print('\n**** os diff of files: ****')
        pp(f'expected_fqfn={self.expected_fqfn}')
        pp(f'actual_fqfn={self.out_fqfn}')



    def load_config(self,
                    example_number):   # ex: 'example-1'

        self.config_fn = pjoin(self.example_dir, f'{example_number}.yml')
        with open(self.config_fn) as buf:
            self.config = yaml.YAML(typ='safe', pure=True).load(buf)

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

        self.config_fn = pjoin(self.example_dir, f'{example_number}.yml')
        self.in_fqfn = glob.glob(pjoin(self.example_dir, f'{example_number}_*_input.csv'))[0]
        self.expected_fqfn = glob.glob(pjoin(self.example_dir, f'{example_number}_*_output.csv'))[0]
        self.out_fqfn = pjoin(self.temp_dir, f'{example_number}_actualout.csv')

        self.cmd = f''' {pjoin(self.script_dir, self.pgm)}   \
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




def executor(cmd,
             expect_success=True,
             output='stdout'):

    runner = envoy.run(cmd)
    status_code = runner.status_code

    print(runner.std_out)
    print(runner.std_err)
    if output != 'stdout':
        with open(output, 'w') as outbuf:
            for rec in runner.std_out:
                outbuf.write(rec)
            for rec in runner.std_err:
                outbuf.write(rec)

    if expect_success:
        assert status_code == 0
    else:
        assert status_code != 0
    return status_code





def make_team_file(temp_dir,
                   dialect,
                   record_cnt):

    fqfn = pjoin(temp_dir, 'testfile.csv')
    name_list = ['smith', 'jones', 'thompson', 'ritchie']
    role_list = ['pm', 'programmer', 'dba', 'sysadmin', 'qa', 'manager']
    proj_list = ['cads53', 'jefta', 'norma', 'us-cepa']

    def get_fields():
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        return name, role, proj

    with open(fqfn, 'w', newline='') as outbuf:
        fieldnames = ['id', 'proj', 'role', 'name']
        writer = csv.DictWriter(outbuf, fieldnames=fieldnames, dialect=dialect)

        if dialect.has_header and record_cnt > 0:
            writer.writeheader()

        for num in range(record_cnt):
            name, role, proj = get_fields()
            writer.writerow({'id': num, 'proj': proj, 'role':role, 'name':name})

    return fqfn
