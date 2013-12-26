#!/usr/bin/env python
""" Provides tools to assist in testing.
"""
import imp
import os
import sys

sys.dont_write_bytecode = True

def load_script(script_name):
    """ loads a script in the parent directory as a module, and passes back
        the module reference.  This is used when there is no .py suffix.

        Inputs:  the name of the script, without a directory
        Outputs: the module reference
    """

    test_dir              = os.path.dirname(os.path.realpath(__file__))
    script_dir            = os.path.dirname(test_dir)
    py_source_open_mode   = "U"
    py_source_description = (".py", py_source_open_mode, imp.PY_SOURCE)
    script_filepath       = os.path.join(script_dir, script_name)
    with open(script_filepath, py_source_open_mode) as script_file:
        mod = imp.load_module(script_name, script_file, script_filepath,  py_source_description)

    return mod


def get_app_root():
    """ returns the application root directory
    """

    test_dir    = os.path.dirname(os.path.realpath(__file__))
    script_dir  = os.path.dirname(test_dir)
    app_dir     = os.path.dirname(script_dir)
    return app_dir


def myprinter(label, value):
      print '%-20.20s:   %s' % (label, value)


def myfileprinter(label, fn, max_recs=20):
      print '%-20.20s ' % fn
      row_cnt = 0
      for row in fileinput.input(fn):
          if max_recs and max_recs <= row_cnt:
              break
          else:
              print row[:-1]
              row_cnt += 1
      fileinput.close()

def get_names_dict(*args):
      id2name = dict((id(val), key) for key, val in
                     inspect.stack()[1][0].f_locals.items())
      return dict((id2name[id(a)], a) for a in args)


def print_whoami():
    name = sys._getframe(1).f_code.co_name
    file = sys._getframe(1).f_code.co_filename
    line = sys._getframe(1).f_lineno
    print 'Function: %s in file: %s at line: %d' % (name, file, line)


