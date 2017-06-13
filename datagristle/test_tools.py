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
      print('%-20.20s:   %s' % (label, value))


def myfileprinter(label, fn, max_recs=20):
      print('%-20.20s ' % fn)
      row_cnt = 0
      for row in fileinput.input(fn):
          if max_recs and max_recs <= row_cnt:
              break
          else:
              print(row[:-1])
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
    print('Function: %s in file: %s at line: %d' % (name, file, line))



def temp_file_remover(fqfn_prefix):
      for temp_file in glob.glob('%s*' % fqfn_prefix):
          os.remove(temp_file)


def generate_7x7_test_file(prefix, hasheader=False, delimiter='|', dirname=None):

    if dirname:
        (fd, fqfn) = tempfile.mkstemp(prefix=prefix, dir=dirname)
    else:
        (fd, fqfn) = tempfile.mkstemp(prefix=prefix)
    dlm = delimiter
    data_7x7 = []
    if hasheader:
        data_7x7.append('col0%(dlm)scol1%(dlm)scol2%(dlm)scol3%(dlm)scol4%(dlm)scol5%(dlm)scol6' % locals())

    data_7x7.append('0-0%(dlm)s0-1%(dlm)s0-2%(dlm)s0-3%(dlm)s0-4%(dlm)s0-5%(dlm)s0-6' % locals())
    data_7x7.append('1-0%(dlm)s1-1%(dlm)s1-2%(dlm)s1-3%(dlm)s1-4%(dlm)s1-5%(dlm)s1-6' % locals())
    data_7x7.append('2-0%(dlm)s2-1%(dlm)s2-2%(dlm)s2-3%(dlm)s2-4%(dlm)s2-5%(dlm)s2-6' % locals())
    data_7x7.append('3-0%(dlm)s3-1%(dlm)s3-2%(dlm)s3-3%(dlm)s3-4%(dlm)s3-5%(dlm)s3-6' % locals())
    data_7x7.append('4-0%(dlm)s4-1%(dlm)s4-2%(dlm)s4-3%(dlm)s4-4%(dlm)s4-5%(dlm)s4-6' % locals())
    data_7x7.append('5-0%(dlm)s5-1%(dlm)s5-2%(dlm)s5-3%(dlm)s5-4%(dlm)s5-5%(dlm)s5-6' % locals())
    data_7x7.append('6-0%(dlm)s6-1%(dlm)s6-2%(dlm)s6-3%(dlm)s6-4%(dlm)s6-5%(dlm)s6-6' % locals())

    fp = os.fdopen(fd,"w")
    for rec in data_7x7:
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn, data_7x7


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

