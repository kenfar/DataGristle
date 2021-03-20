#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
   Copyright 2011-2021 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import os
from os.path import dirname, join as pjoin
from pprint import pprint as pp
import sys

import datagristle.test_tools as test_tools

pgm_path = dirname(dirname(os.path.realpath((__file__))))
MOD = test_tools.load_script(pjoin(pgm_path, 'gristle_differ'))


class TestGetAssignWithOffsetsForNames(object):

    def test_basics(self):
        col_names = ['col0', 'col1', 'col2', 'col3']
        config = [{"dest_file":"insert", "dest_field":"col0", "src_type":"copy",
                   "src_file":"old", "src_field":"col0"}]
        target_config = [{"dest_file":"insert", "dest_field":0,
                          "src_type":"copy",
                          "src_file":"old", "src_field":0}]
        print('target: ')
        pp(target_config)
        print('results: ')
        pp(MOD.get_assign_with_offsets_for_names(col_names, config))
        assert MOD.get_assign_with_offsets_for_names(col_names, config) == target_config
