#!/usr/bin/env python
"""
   See the file "LICENSE" for the full license governing this code. 
   Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import random
import csv
import optparse
import pytest
from pprint import pprint as pp
import test_tools

mod = test_tools.load_script('gristle_file_converter')




class TestOptsAndArgs(object):

   def _run_check(self, sysarg, expected_result):
       sys.argv       = sysarg
       cmd_parser     = None
       opts           = None
       files          = None
       if expected_result == 'SystemExit':
           with pytest.raises(SystemExit):
               cmd_parser = mod.CommandLineParser()
               opts       = cmd_parser.opts
               files      = cmd_parser.files
       elif expected_result == 'except':
           with pytest.raises(Exception):
               cmd_parser = mod.CommandLineParser()
               opts       = cmd_parser.opts
               files      = cmd_parser.files
       elif expected_result == 'pass':
           try:
               cmd_parser = mod.CommandLineParser()
               opts       = cmd_parser.opts
               files      = cmd_parser.files
           except:
               pytest.fail('cmd had exception - when none was expected')

       return cmd_parser, opts, files



   def test_goaa_happy_path(self):
       parser, opts, files = self._run_check(['../gristle_file_converter.py', 'census.csv', '-d', ',', '-D', '|'], 'pass')

       assert opts.output           is None
       assert opts.recdelimiter     is None
       assert opts.delimiter        == ','
       assert opts.out_delimiter    == '|'
       assert opts.recdelimiter     is None
       assert opts.out_recdelimiter is None
       assert opts.quoting          is False
       assert opts.out_quoting      is False
       assert opts.quotechar        == '"'
       assert opts.hasheader        is False
       assert opts.out_hasheader    is False
       assert opts.stripfields      is False
       assert opts.verbose          is True

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








