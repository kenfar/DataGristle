#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""
import sys
import os
import tempfile
import random
import atexit
import shutil
import pytest
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))
sys.path.insert(0, dirname(dirname(os.path.abspath(__file__))))
import datagristle.common  as mod


class TestFunctions(object):

    def test_get_common_key(self):
        d = {'car': 7, 'truck':8, 'boat':30, 'plane': 5}
        assert mod.get_common_key(d) == ('boat',0.6)


class Test_colnames_to_coloff0(object):

    def test_empty_lists(self):
        assert mod.colnames_to_coloff0([], []) == []

    def test_col_numbers_only(self):
        assert mod.colnames_to_coloff0([], [0,3,5]) == [0,3,5]

    def test_string_lookuplist_int_namelist(self):
        assert mod.colnames_to_coloff0(['0','1','2'], [0]) == [0]

    def test_int_lookuplist_string_namelist(self):
        assert mod.colnames_to_coloff0([0,1,2], ['0']) == [0]

    def test_col_numbers_strings_only(self):
        assert mod.colnames_to_coloff0([], ['0','3','5']) == [0,3,5]

    def test_col_all_names_only(self):
        assert mod.colnames_to_coloff0(['foo', 'bar', 'baz'], ['foo', 'bar', 'baz']) == [0,1,2]

    def test_col_some_names_only(self):
        assert mod.colnames_to_coloff0(['foo', 'bar', 'baz'], ['bar']) == [1]

    def test_col_mix_of_names_and_numbers(self):
        assert mod.colnames_to_coloff0(['foo', 'bar', 'baz'], [0, 'bar', 'baz']) == [0,1,2]

    def test_error_name_not_found(self):
        with pytest.raises(KeyError):
            assert mod.colnames_to_coloff0(['foo', 'bar', 'baz'], ['gorilla'])

    def test_error_number_not_found(self):
        with pytest.raises(KeyError):
            assert mod.colnames_to_coloff0(['foo', 'bar', 'baz'], [5])





