#!/usr/bin/env python
"""
   See the file "LICENSE" for the full license governing this code. 
   Copyright 2011,2012,2013 Ken Farmer
"""


import sys
import os
import tempfile
import random
import unittest
import csv
import optparse
from pprint import pprint as pp
import test_tools
mod = test_tools.load_script('gristle_file_converter')



def main():

    opts, args = get_opts()

    if opts.suite == 'fast':
        test_suite = fast_suite()
    else:
        test_suite = slow_suite()

    if not opts.verbose:
        # shut off the printing of warnings & info statements from module
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        null       = open(os.devnull, 'wb')
        sys.stdout = sys.stderr = null

    runner = unittest.TextTestRunner()
    runner.run(test_suite)



def get_opts():
    use    = ('Runs all tests for gristle_file_converter.py. '
              'use arg of fast or slow to control comprehensiveness.')
    parser = optparse.OptionParser(usage=use)
    parser.add_option('-s','--suite',
           default='fast',
           choices=['fast','slow'],
           help='Options are fast & slow - which control which tests are performed.  Default is fast.')
    parser.add_option('-v','--verbose',
           default=False,
           action='store_true',
           help='Turns on verbose details.  Default is off')
    opts, args = parser.parse_args()
    return opts, args



def fast_suite():

    print 'running FAST suite'
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test_get_opts_and_args))

    return suite



def slow_suite():

    print 'running SLOW suite'
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test_get_opts_and_args))

    return suite




class test_get_opts_and_args(unittest.TestCase):

   def _run_check(self, sysarg, expected_result):
       sys.argv = sysarg
       cmd_parser     = None
       opts           = None
       files          = None
       try:
           cmd_parser = mod.CommandLineParser()
           opts       = cmd_parser.opts
           files      = cmd_parser.files
       except SystemExit:
           if expected_result != 'SystemExit':
               raise
               self.fail('unexpected SystemExit exception thrown')
       except:
           if expected_result != 'except':
               self.fail('unexpected exception thrown')
       else:
           if expected_result != 'pass':
               self.fail('expected exception not thrown')
       return cmd_parser, opts, files

   def test_goaa_happy_path(self):
       parser, opts, files = self._run_check(['../gristle_file_converter.py', 'census.csv', '-d', ',', '-D', '|'], 'pass')

       assert(opts.output           is None)
       assert(opts.recdelimiter     is None)
       assert(opts.delimiter        == ',')
       assert(opts.out_delimiter    == '|')
       assert(opts.recdelimiter     is None)
       assert(opts.out_recdelimiter is None)
       assert(opts.quoting          is False)
       assert(opts.out_quoting      is False)
       assert(opts.quotechar        == '"')
       assert(opts.hasheader        is False)
       assert(opts.out_hasheader    is False)
       assert(opts.stripfields      is False)
       assert(opts.verbose          is True)

       self._run_check(['../gristle_file_converter.py', 'census4.csv', '-D', '|'], 'pass')
       self._run_check(['../gristle_file_converter.py', 'census5.csv', '-d',',','-D', '|'], 'pass')
       self._run_check(['../gristle_file_converter.py', 'census6.csv', '-d',',','-D', '|', '--hasheader','--outhasheader'], 'pass')
       self._run_check(['../gristle_file_converter.py', 'census6.csv', '-D', '|', '-r','-R','-q', '-Q','--quotechar','^'], 'pass')
       self._run_check(['../gristle_file_converter.py', 'census6.csv', '-D', '|', '--stripfields'], 'pass')

   def test_goaa_check_missing_out_del(self):
       self._run_check(['../gristle_file_converter.py', 'census.csv'], 'SystemExit')         # missing out delimiter
   def test_goaa_check_missing_out_del_arg(self):
       self._run_check(['../gristle_file_converter.py', 'census.csv', '-D'], 'SystemExit')   # missing arg
   def test_goaa_check_unknown_option(self):
       self._run_check(['../gristle_file_converter.py', 'census.csv', '-X'], 'SystemExit')   # unknown value (x)
   def test_goaa_check_multi_file_no_options(self):
       self._run_check(['../gristle_file_converter.py', 'census1.csv', 'census2.csv'], 'SystemExit')
        
    






if __name__ == "__main__":
    main()





