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


def suite():

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOptsAndArgs))
    unittest.TextTestRunner(verbosity=2).run(suite)

    return suite




class TestOptsAndArgs(unittest.TestCase):

   def _run_check(self, sysarg, expected_result):
       sys.argv       = sysarg
       cmd_parser     = None
       opts           = None
       files          = None
       try:
           cmd_parser = mod.CommandLineParser()
           opts       = cmd_parser.opts
           files      = cmd_parser.files
       except SystemExit:
           if expected_result != 'SystemExit':
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

       self.assertTrue(opts.output           is None)
       self.assertTrue(opts.recdelimiter     is None)
       self.assertTrue(opts.delimiter        == ',')
       self.assertTrue(opts.out_delimiter    == '|')
       self.assertTrue(opts.recdelimiter     is None)
       self.assertTrue(opts.out_recdelimiter is None)
       self.assertTrue(opts.quoting          is False)
       self.assertTrue(opts.out_quoting      is False)
       self.assertTrue(opts.quotechar        == '"')
       self.assertTrue(opts.hasheader        is False)
       self.assertTrue(opts.out_hasheader    is False)
       self.assertTrue(opts.stripfields      is False)
       self.assertTrue(opts.verbose          is True)

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
    unittest.main(suite())





