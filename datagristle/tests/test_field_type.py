#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""

import sys
import os
import tempfile
import random
import pytest
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))
sys.path.insert(0, dirname(dirname(os.path.abspath(__file__))))

import datagristle.field_type  as mod



class TestIsInteger(object):

    def test_is_integer_basics(self):
        assert mod.is_integer('3')
        assert mod.is_integer('-3')
        assert mod.is_integer(3)
        assert mod.is_integer(-3)
        assert mod.is_integer(3.0)
        assert mod.is_integer('b')        is False
        assert mod.is_integer('')         is False
        assert mod.is_integer(' ')        is False
        assert mod.is_integer('$3')       is False
        assert mod.is_integer('4,333.22') is False
        assert mod.is_integer('33.22')    is False
        assert mod.is_integer(3.3)        is False
        assert mod.is_integer(None)       is False


class TestIsFloat(object):

    def test_is_float_basics(self):
        assert mod.is_float('33.22')
        assert mod.is_float(44.55)
        assert mod.is_float(44.0)        is False
        assert mod.is_float(3)           is False
        assert mod.is_float(0.0)         is False
        assert mod.is_float(0)           is False
        assert mod.is_float('b')         is False
        assert mod.is_float('')          is False
        assert mod.is_float(' ')         is False
        assert mod.is_float('$3')        is False
        assert mod.is_float('4,333.22')  is False
        assert mod.is_float('3')         is False
        assert mod.is_float('-3')        is False
        assert mod.is_float(None)        is False


class TestIsString(object):

    def test_is_string_basics(self):
        assert mod.is_string('b')
        assert mod.is_string('')
        assert mod.is_string(' ')
        assert mod.is_string('$3')
        assert mod.is_string('4,333.22')
        assert mod.is_string('33.22')     is False
        assert mod.is_string('3')         is False
        assert mod.is_string('-3')        is False
        assert mod.is_string(3)           is False
        assert mod.is_string(3.3)         is False
        assert mod.is_string(None)        is False

class TestIsUnknown(object):

    def test_is_unknown_basics(self):
        assert mod.is_unknown('')
        assert mod.is_unknown(' ')
        assert mod.is_unknown('na')
        assert mod.is_unknown('NA')
        assert mod.is_unknown('n/a')
        assert mod.is_unknown('N/A')
        assert mod.is_unknown('unk')
        assert mod.is_unknown('unknown')
        assert mod.is_unknown('b')         is False
        assert mod.is_unknown('$3')        is False
        assert mod.is_unknown('4,333.22')  is False
        assert mod.is_unknown('33.22')     is False
        assert mod.is_unknown('3')         is False
        assert mod.is_unknown('-3')        is False
        assert mod.is_unknown(3)           is False
        assert mod.is_unknown(3.3)         is False
        assert mod.is_unknown(None)        is False


class TestIsTimestamp(object):

    def runner(self, date):
        result, scope, pattern = mod.is_timestamp(date)
        return result, scope

    def test_is_timestamp_bad_dates(self):
        assert self.runner("0")         == (False, None)
        assert self.runner("-4")        == (False, None)
        assert self.runner("-4.7")      == (False, None)
        assert self.runner("blah")      == (False, None)
        assert self.runner("blah")      == (False, None)
        assert self.runner("2009 ")     == (False, None)
        assert self.runner("2009 ")     == (False, None)

        assert self.runner("2009-10-06-18") == (True, 'hour')
        assert self.runner("2009-10-06-03.02.01") == (True, 'second')

    def test_is_timestamp_good_dates(self):
        assert self.runner("1172969203.1")   == (True, 'second')

        assert self.runner("2009")   == (True, 'year')

        assert self.runner("200910") == (True, 'month')
        assert self.runner("2009-10") == (True, 'month')

        assert self.runner("20090206")     == (True, 'day')
        assert self.runner("2009-10-06") == (True, 'day')
        assert self.runner("10/26/09")   == (True, 'day')
        assert self.runner("10-26-09")   == (True, 'day')
        assert self.runner("26/10/09")   == (True, 'day')
        assert self.runner("26-10-09")   == (True, 'day')
        assert self.runner("10/26/2009") == (True, 'day')
        assert self.runner("10-26-2009") == (True, 'day')
        assert self.runner("26/10/2009") == (True, 'day')
        assert self.runner("26-10-2009") == (True, 'day')
        assert self.runner("Feb 13,2009") == (True, 'day')
        assert self.runner("Feb 13, 2009") == (True, 'day')
        assert self.runner("February 13,2009") == (True, 'day')
        assert self.runner("February 13, 2009") == (True, 'day')
        assert self.runner("2009-10-06 18") == (True, 'hour')
        assert self.runner("2009-10-06-18") == (True, 'hour')
        assert self.runner("2009-10-06 18:10") == (True, 'minute')
        assert self.runner("2009-10-06-18.10") == (True, 'minute')
        assert self.runner("2009-10-06 03:02:01") == (True, 'second')
        assert self.runner("2009-10-06 00:00:00") == (True, 'second')
        assert self.runner("2009-10-06 03:02:01.01") == (True, 'microsecond')
        assert self.runner("2009-10-06 03:02:01.01234") == (True, 'microsecond')



class TestGetType(object):

    def test_get_type_basics(self):
        assert mod._get_type('n/a')  == 'unknown'
        assert mod._get_type('UNK')  == 'unknown'
        assert mod._get_type('unk')  == 'unknown'
        assert mod._get_type(' ')    == 'unknown'
        assert mod._get_type('')     == 'unknown'
        assert mod._get_type('0')    == 'integer'
        assert mod._get_type('1')    == 'integer'
        assert mod._get_type('-1')   == 'integer'
        assert mod._get_type('+1')   == 'integer'
        assert mod._get_type('1.1')  == 'float'
        assert mod._get_type('blah') == 'string'



class TestGetFieldType(object):


    def test_get_field_type_basics(self):
        assert mod.get_field_type(None)         == 'unknown'
        assert mod.get_field_type([])           == 'unknown'
        assert mod.get_field_type({})           == 'unknown'
        assert mod.get_field_type({'Texas': 4}) == 'string'
        assert mod.get_field_type(['1'])        == 'integer'
        assert mod.get_field_type(['n/a', 'Texas']) == 'string'
        assert mod.get_field_type(['n/a', '55']) == 'integer'
        assert mod.get_field_type(['n/a', '55.5']) == 'float'
        assert mod.get_field_type(['n/a', ''])  == 'unknown'
        assert mod.get_field_type(['n/a', '1310527566.7']) == 'timestamp'
        assert mod.get_field_type(['4.3', '1310527566.7']) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     '1.1':   4}
        assert mod.get_field_type(test_data) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     'blah':  4}
        assert mod.get_field_type(test_data) == 'unknown'

        test_data = {'n/a':   3,
                     'blah':  2,
                     '0':     2,
                     '1.1':   4}
        assert mod.get_field_type(test_data)  == 'unknown'

    def test_get_field_type_mostly_strings(self):
        test_data = {'n/a':     1,
                     'blah':  999,
                     '0':       1,
                     '1.1':     1,
                     '2011-04': 1}
        assert mod.get_field_type(test_data)  == 'string'





