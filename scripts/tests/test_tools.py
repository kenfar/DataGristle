#!/usr/bin/env python
""" Provides tools to assist in testing.
"""
import imp
import os
import sys
import tempfile
import glob

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



def temp_file_remover(fqfn_prefix):
      for temp_file in glob.glob('%s*' % fqfn_prefix):
          os.remove(temp_file)


def generate_7x7_test_file(prefix, hasheader=False):
    (fd, fqfn) = tempfile.mkstemp(prefix=prefix)

    data_7x7 = []
    if hasheader:
        data_7x7.append('col0|col1|col2|col3|col4|col5|col6')

    data_7x7.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')
    data_7x7.append('1-0|1-1|1-2|1-3|1-4|1-5|1-6')
    data_7x7.append('2-0|2-1|2-2|2-3|2-4|2-5|2-6')
    data_7x7.append('3-0|3-1|3-2|3-3|3-4|3-5|3-6')
    data_7x7.append('4-0|4-1|4-2|4-3|4-4|4-5|4-6')
    data_7x7.append('5-0|5-1|5-2|5-3|5-4|5-5|5-6')
    data_7x7.append('6-0|6-1|6-2|6-3|6-4|6-5|6-6')

    fp = os.fdopen(fd,"w")
    for rec in data_7x7:
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn, data_7x7
