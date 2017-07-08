#!/usr/bin/env python
""" Provides tools to assist in testing.
"""
import imp
import os
import sys
import tempfile
import glob

sys.dont_write_bytecode = True


def load_script(script_name: str):
    """ loads a script in the parent directory as a module, and passes back
        the module reference.  This is used when there is no .py suffix.

        Inputs:  the name of the script, without a directory
        Outputs: the module reference
    """
    test_dir = os.path.dirname(os.path.realpath(__file__))
    script_dir = os.path.dirname(test_dir)
    py_source_open_mode = "U"
    py_source_description = (".py", py_source_open_mode, imp.PY_SOURCE)
    script_filepath = os.path.join(script_dir, script_name)
    with open(script_filepath, py_source_open_mode) as script_file:
        mod = imp.load_module(script_name, script_file, script_filepath,  py_source_description)

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
