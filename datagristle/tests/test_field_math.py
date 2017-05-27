#!/usr/bin/env python
"""
    To do:
      1.  add tests for floats

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import random
from pprint import pprint
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))
sys.path.insert(0, dirname(dirname(os.path.abspath(__file__))))
import datagristle.field_math  as mod


class TestGetMedian(object):

    def test_empty(self):
        values = []
        assert mod.get_median(values) == None

    def test_single_value(self):
        values = [(3, 1)]
        assert mod.get_median(values) == 3

    def test_single_entry_two_occurances(self):
        values = [(3, 2)]
        assert mod.get_median(values) == 3

    def test_single_entry_three_occurances(self):
        values = [(3, 3)]
        assert mod.get_median(values) == 3

    def test_two_entries_with_one_occurence_each(self):
        values = [(1, 1), (2, 1)]
        assert mod.get_median(values) == 1.5

    def test_even_number_of_values_with_one_occurances_each(self):
        values = [(1, 1), (2, 1), (6, 1), (5, 1), (4, 1), (3, 1)]
        assert mod.get_median(values) == 3.5

    def test_even_number_of_values_with_three_occurances_each(self):
        values = [(1, 3), (2, 3), (6, 3), (5, 3), (4, 3), (3, 3)]
        assert mod.get_median(values) == 3.5

    def test_odd_number_of_values_with_one_occurances_each(self):
        values = [(1, 1), (2, 1), (5, 1), (4, 1), (3, 1)]
        assert mod.get_median(values) == 3

    def test_odd_number_of_values_with_three_occurances_each(self):
        values = [(1, 3), (2, 3), (6, 3), (5, 3), (4, 3), (3, 3)]
        assert mod.get_median(values) == 3.5

    def test_odd_number_with_skew(self):
        values = [(1, 10), (2, 4), (6, 3), (5, 2), (4, 1), (3, 1)]
        assert mod.get_median(values) == 2

    def test_even_number_with_skew(self):
        values = [(1, 10), (2, 4), (6, 3), (5, 2), (4, 1)]
        assert mod.get_median(values) == 1.5

    def test_odds_and_even_numbers(self):
        values = [(-1, 1), (1, 1)]
        assert mod.get_median(values) == 0

    def test_floats(self):
        values = [(0.1, 1), (0.3, 1)]
        assert mod.get_median(values) == 0.2

    def test_alpha_values(self):
        values = [('foo', 1), (4, 1)]
        assert mod.get_median(values) == 4

    def test_none_values(self):
        values = [(None, 1), (4, 1)]
        assert mod.get_median(values) == 4

    def test_dictionary(self):
        values = {1: 1, 2:1}
        assert mod.get_median(values) == 1.5

    def test_types(self):
        assert type(mod.get_median({10:4, 100:86}))  is float
        assert type(mod.get_median({1:1})) is float





class Test_get_variance_and_stddev(object):

    def setup_method(self, method):
        # suffix of 'a' indicates the answer
        pass

    def _convert_float(self, value):
        return  '%.2f' % value

    def test_math_empty_list(self):
        list_1   = {}
        list_1a  = (None, None)
        assert mod.get_variance_and_stddev(list_1) == list_1a

    def test_math_identical_single_number_occuring_once(self):

        list_1   = {2:1}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)    == list_1a

        list_2   = {2:1, 2:1,2:1}
        list_2a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_2, 2) == list_2a
        assert mod.get_variance_and_stddev(list_2)    == list_2a

    def test_math_multiple_numbers_occuring_once(self):

        list_1   = {2:1, 3:1, 4:1}
        list_1a  = ('0.67', '0.82')
        var, stddev  = mod.get_variance_and_stddev(list_1)
        small_var    = self._convert_float(var)
        small_stddev = self._convert_float(stddev)
        assert (small_var, small_stddev) == list_1a

        list_2   = {2:1, 3:1, 9:1, 12:1, 13:1, 15:1,
                   17:1, 19:1, 22:1, 23:1, 25:1}
        list_2a  = ('53.88', '7.34')
        var, stddev  = mod.get_variance_and_stddev(list_2)
        small_var    = self._convert_float(var)
        small_stddev = self._convert_float(stddev)
        assert (small_var, small_stddev) == list_2a

    def test_math_multiple_numbers_occurring_multiple_times(self):
        list_4   = {2:10, 3:15, 9:10, 12:7, 13:4, 15:2,
                   17:1, 19:1, 22:1, 23:1, 25:1}
        list_4a  = ('37.11', '6.09')
        var, stddev  = mod.get_variance_and_stddev(list_4)
        small_var    = self._convert_float(var)
        small_stddev = self._convert_float(stddev)
        assert (small_var, small_stddev) == list_4a

    def test_math_identical_single_float_occuring_once(self):
        list_1   = {2.0:1}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)    == list_1a

        list_2   = {2.5:1}
        list_2a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_2, 2.5) == list_2a
        assert mod.get_variance_and_stddev(list_2)      == list_2a


    def test_math_floats_multiple_floats_occuring_once(self):

        list_1   = {2.0:1, 3.0:1, 4.0:1}
        list_1a  = ('0.67', '0.82')
        var, stddev  = mod.get_variance_and_stddev(list_1)
        small_var    = self._convert_float(var)
        small_stddev = self._convert_float(stddev)
        assert (small_var, small_stddev) == list_1a

    def test_math_single_float_occurring_multiple_times(self):
        list_1   = {2.5:2}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2.5) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

    def test_math_single_string_occurring_once(self):
        list_1   = {'2':2}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

        list_1   = {'2':2}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

    def test_math_ignoring_bad_key(self):
        list_1   = {2:2, 'bar':2}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

    def deprecatedtest_math_ignoring_bad_value(self):
        list_1   = {2:2, 3:'foo'}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a




class TestGetMean(object):

    def test_none(self):
        assert mod.get_mean(None) is None

    def test_emptiness(self):
        assert mod.get_mean({}) is None

    def test_alpha_values(self):
        assert mod.get_mean({'blah':2}) == 0

    def test_mean_of_numbers_in_string_format(self):
        assert mod.get_mean({'10':4, '100':86})  == 96.00

    def test_mean_of_ints(self):
        assert mod.get_mean({10:4, 100:86})  == 96.00

    def test_list_of_tuples(self):
        assert mod.get_mean([(10,4), (15, 4)]) == 12.5

    def test_mean_of_floats(self):
        assert mod.get_mean({2.5:4, 10:1})  == 4.0

    def test_mean_of_numbers_in_string_format(self):
        test_dict  = {2:1,3:1,9:1,12:1,13:1,15:1,17:1,19:1,22:1,23:1,25:1}
        result = '%.4f' % mod.get_mean(test_dict)
        assert result  == str(14.5455)

    def test_types(self):
        assert mod.get_mean({10:4, 100:86})  == 96.00
        assert mod.get_mean({1:1})  == 1



class TestGetMeanLength(object):

    def test_empty(self):
        assert mod.get_mean_length({}) is None

    def test_none(self):
        assert mod.get_mean_length(None) is None

    def test_unknowns(self):
        assert mod.get_mean_length({'UNK':1, 'unknown':3, ' ':99, '':99, 'a':4, 'b':2}) == 1

    def test_easy_singles(self):
        assert mod.get_mean_length({'abc':1, 'abcdefg':1}) == 5

    def test_easy_multiples(self):
        assert mod.get_mean_length({'abc':99, 'abcdef':1}) == 3.03

    def test_list_of_tuples(self):
        assert mod.get_mean_length([('abc',99), ('abcdef',1)]) == 3.03




