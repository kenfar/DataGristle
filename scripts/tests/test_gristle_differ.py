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

mod = test_tools.load_script('gristle_differ')


class Test_get_assign_with_offsets_for_names(object):

  def test_basics(self):
      col_names = ['col0', 'col1', 'col2', 'col3']
      config    = [{"dest_file":"insert", "dest_field":"col0", "src_type":"copy",
                    "src_file":"old",  "src_field":"col0"}]
      target_config = [{"dest_file":"insert", "dest_field":0, "dest_field_orig":"col0",
                        "src_type":"copy",
                        "src_file":"old",  "src_field":0, "src_field_orig":"col0"}]
      print('target: ')
      pp(target_config)
      print('results: ')
      pp(mod.get_assign_with_offsets_for_names(col_names, config))
      assert mod.get_assign_with_offsets_for_names(col_names, config) == target_config

