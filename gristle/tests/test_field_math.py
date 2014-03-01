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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.field_math  as mod



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

        list_1   = {'2':'2'}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

    def test_math_ignoring_bad_key(self):
        list_1   = {2:2, 'bar':2}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a

    def test_math_ignoring_bad_value(self):
        list_1   = {2:2, 3:'foo'}
        list_1a  = (0.0, 0.0)
        assert mod.get_variance_and_stddev(list_1, 2) == list_1a
        assert mod.get_variance_and_stddev(list_1)      == list_1a


class TestGetDictMedian(object):

    def setup_method(self, method):
        # suffix of 'a' indicates the answer
        self.dict_1   = {}
        self.dict_1a  = None
        self.dict_2   = {'1':1, '2':1, '3':1, '4':1, '100':99 }
        self.dict_2a  = 100
        self.dict_3   = {'2':3, '4':3}
        self.dict_3a  = 3
        self.dict_4   = {'1':3, '4':1}
        self.dict_4a  = 1

        self.mymed         =  mod.GetDictMedian()

    def test_math_a02_dicts(self):
        #print self.mymed.run(self.med_dict_1)
        assert self.mymed.run(self.dict_1) == self.dict_1a
        assert self.mymed.run(self.dict_2) == self.dict_2a
        assert self.mymed.run(self.dict_3) == self.dict_3a
        assert self.mymed.run(self.dict_4) == self.dict_4a



class Test_get_tuple_list(object):
    def setup_method(self, method):
        self.mymed         =  mod.GetDictMedian()

    def test_math_b01_emptiness(self):
        self.dict_1        = {}
        self.dict_1a       = None
        assert self.mymed.run(self.dict_1) == self.dict_1a 

    def test_math_b02(self):
        self.dict_2        = {'8': 3, '1': 2, '4': 4}
        self.dict_2a       = [('1',2),('4',4),('8',3)]
        tup_list = self.mymed._get_tuple_list(self.dict_2)
        assert sorted(tup_list) == sorted(self.dict_2a)

    def test_math_b03(self):
        self.dict_3        = {'8':1, '1':1, '4':1 }
        self.dict_3a       = [('1',1),('4',1),('8',1)]
        tup_list = self.mymed._get_tuple_list(self.dict_3)
        assert sorted(tup_list) == self.dict_3a



class Test_get_numeric_tuple_list(object):
    def setup_method(self, method):
        # suffix of 'a' indicates the answer
        self.mymed         =  mod.GetDictMedian()
        self.list_1        = []
        self.list_1a       = []
        self.list_2        = [('8','1')]
        self.list_2a       = [(8,1)]
        self.list_3        = [('8',1),(1,'1'),('4','1')]
        self.list_3a       = [(8,1),(1,1),(4,1)]
        self.list_4        = [('8','1'),('a',1),(4,'b')]
        self.list_4a       = [(8,1)]

    def test_math_c01(self):
        assert self.mymed._get_numeric_tuple_list(self.list_1) == self.list_1a
        assert self.mymed._get_numeric_tuple_list(self.list_2) == self.list_2a
        assert self.mymed._get_numeric_tuple_list(self.list_3) == self.list_3a
        assert self.mymed._get_numeric_tuple_list(self.list_4) == self.list_4a


class Test_get_median_subs(object):
    def setup_method(self, method):
        # suffix of 'a' indicates the answer
        self.mymed         =  mod.GetDictMedian()
    def test_math_d01(self):
        assert self.mymed._get_median_subs(0) == (0,0)
        assert self.mymed._get_median_subs(1) == (0,0)
        assert self.mymed._get_median_subs(2) == (0,1)
        assert self.mymed._get_median_subs(3) == (1,1)
        assert self.mymed._get_median_subs(4) == (1,2)
        assert self.mymed._get_median_subs(5) == (2,2)
        assert self.mymed._get_median_subs(6) == (2,3)
        assert self.mymed._get_median_subs(7) == (3,3)
        assert self.mymed._get_median_subs(8) == (3,4)


class Test_get_median_keys(object):
    """ Desc: test the ability to provide a sorted list of tuples and a key
              and have the function go through the keys, and key occurances,
    """
    def setup_method(self, method):
        # suffix of 'a' indicates the answer
        self.mymed         =  mod.GetDictMedian()
        self.med_1         = [(1,1),(4,1),(4,1)]
        self.med_2         = [(1,1),(4,1),(8,1)]
        self.med_3         = [(1,1)]
        self.hard_1        = [(1,6),(4,1),(8,1)]
        self.hard_2        = [(1,5),(4,1),(8,1)]
        self.hard_3        = [(1,2),(4,1),(8,1),(10,1),(99,1),(99,1)]

    def test_math_e01(self):
        assert self.mymed._get_median_keys(self.med_1,  1) == 4
        assert self.mymed._get_median_keys(self.med_2,  1) == 4
        assert self.mymed._get_median_keys(self.med_3,  0) == 1
        assert self.mymed._get_median_keys(self.hard_1, 1) == 1
        assert self.mymed._get_median_keys(self.hard_2, 3) == 1
        assert self.mymed._get_median_keys(self.hard_3, 3) == 8



class TestGetMean(object):

    def setup_method(self, method):
        self.empty_dict_1  = {}
        self.empty_dict_2  = {'blah':2}
        self.easy_dict   = {'8': 3, '1': 2, '3': 4}
        self.unk_dict    = {'UNK':1, 'unknown':3, ' ':99, '8':4, '2':2 }
        self.med_dict_1  = {'10':4, '100':86 }
        self.med_dict_3  = {2:1,3:1,9:1,12:1,13:1,15:1,
                            17:1,19:1,22:1,23:1,25:1}

    def test_math_f01_emptiness(self):
        assert mod.get_mean(self.empty_dict_1) is None
        assert mod.get_mean(self.empty_dict_2) is None

    def test_math_f03_small_sets(self):
        pass

    def test_math_f04_medium_sets(self):
        assert mod.get_mean(self.med_dict_1)  == 96.00
        result = '%.4f' % mod.get_mean(self.med_dict_3)
        assert result  == str(14.5455)



class Test_get_mean_length(object):

    def setup_method(self, method):
        self.empty_dict_1 = {}
        self.easy_dict    = {'8': 3, '1': 2, '3': 4}
        self.unk_dict     = {'UNK':1, 'unknown':3, ' ':99, '8':4, '2':2 }
        self.med_dict_1   = {'aaa':1, 'a':3 }

    def test_math_g01_emptiness(self):
        assert mod.get_mean_length(self.empty_dict_1) is None

    def test_math_g02_unknowns(self):
        assert mod.get_mean_length(self.unk_dict)    == 1

    def test_math_g03_easy_list(self):
        pass

    def test_math_g04_small_sets(self):
        pass

    def test_math_g05_medium_sets(self):
        assert mod.get_mean_length(self.med_dict_1)  == 1.5




