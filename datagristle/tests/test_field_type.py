#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

from pprint import pprint as pp

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
        assert mod.is_float(44.0) is False
        assert mod.is_float(3) is False
        assert mod.is_float(0.0) is False
        assert mod.is_float(0) is False
        assert mod.is_float('b') is False
        assert mod.is_float('') is False
        assert mod.is_float(' ') is False
        assert mod.is_float('$3') is False
        assert mod.is_float('4,333.22') is False
        assert mod.is_float('3') is False
        assert mod.is_float('-3') is False
        assert mod.is_float(None) is False


class TestIsString(object):

    def test_is_string_basics(self):
        assert mod.is_string('b')
        assert mod.is_string('')
        assert mod.is_string(' ')
        assert mod.is_string('$3')
        assert mod.is_string('4,333.22')
        assert mod.is_string('33.22') is False
        assert mod.is_string('3') is False
        assert mod.is_string('-3') is False
        assert mod.is_string(3) is False
        assert mod.is_string(3.3) is False
        assert mod.is_string(None) is False


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
        assert mod.is_unknown('b') is False
        assert mod.is_unknown('$3') is False
        assert mod.is_unknown('4,333.22') is False
        assert mod.is_unknown('33.22') is False
        assert mod.is_unknown('3') is False
        assert mod.is_unknown('-3') is False
        assert mod.is_unknown(3) is False
        assert mod.is_unknown(3.3) is False
        assert mod.is_unknown(None) is False


class TestIsTimestamp(object):

    def runner(self, date):
        return mod.is_timestamp(date)

    def test_unsupported_timestamps_and_non_timestamps(self):
        assert self.runner("0") is False
        assert self.runner("-4") is False
        assert self.runner("-4.7") is False
        assert self.runner("blah") is False
        assert self.runner("blah") is False
        assert self.runner("2009 ") is False
        assert self.runner("2009 ") is False
        assert self.runner("1172969203.1") is False
        assert self.runner("2009") is False
        assert self.runner("200910") is False
        assert self.runner("2009-10") is False
        assert self.runner("20090206") is False

    def test_unsupported_periods(self):
        assert self.runner("2009-10-06-18.10") is False
        assert self.runner("2009-10-06-03.02.01") is False

    def test_dates(self):
        assert self.runner("10/26/09") is True
        assert self.runner("10-26-09") is True
        assert self.runner("26/10/09") is True
        assert self.runner("26-10-09") is True
        assert self.runner("10/26/2009") is True
        assert self.runner("10-26-2009") is True
        assert self.runner("26/10/2009") is True
        assert self.runner("26-10-2009") is True

    def test_month_names(self):
        assert self.runner("Feb 13,2009") is True
        assert self.runner("Feb 13, 2009") is True
        assert self.runner("February 13,2009") is True
        assert self.runner("February 13, 2009") is True

    def test_iso8601(self):
        assert self.runner("2009-10-06") is True
        assert self.runner("2009-10-06t18") is True
        assert self.runner("2009-10-06T18:10") is True
        assert self.runner("2009-10-06T03:02:01") is True
        assert self.runner("2009-10-06T03:02:01.01234") is True

    def test_non_iso8601_timestamps(self):
        assert self.runner("2009-10-06 18") is True
        assert self.runner("2009-10-06-18") is True
        assert self.runner("2009-10-06 18:10") is True
        assert self.runner("2009-10-06-18:10") is True
        assert self.runner("2009-10-06 03:02:01") is True
        assert self.runner("2009-10-06 00:00:00") is True
        assert self.runner("2009-10-06-03:02:01") is True
        assert self.runner("2009-10-06 03:02:01.01") is True
        assert self.runner("2009-10-06 03:02:01.01234") is True
        assert self.runner("2009-10-06-03:02:01.01234") is True

    def test_timezone_z(self):
        assert self.runner("2009-10-06T03:02:01.01234Z") is True
        assert self.runner("2009-10-06T03:02:01Z") is True

    def test_timezone_plus(self):
        assert self.runner("2009-10-06T03:02:01.01234+0700") is True
        assert self.runner("2009-10-06T03:02:01+0700") is True

    def test_timezone_dash(self):
        assert self.runner("2009-10-06T03:02:01.01234-0700") is True
        assert self.runner("2009-10-06T03:02:01-0700") is True





class TestGetType(object):

    def test_get_type_basics(self):
        assert mod._get_type('n/a') == 'unknown'
        assert mod._get_type('UNK') == 'unknown'
        assert mod._get_type('unk') == 'unknown'
        assert mod._get_type(' ') == 'unknown'
        assert mod._get_type('') == 'unknown'
        assert mod._get_type('0') == 'integer'
        assert mod._get_type('1') == 'integer'
        assert mod._get_type('-1') == 'integer'
        assert mod._get_type('+1') == 'integer'
        assert mod._get_type('1.1') == 'float'
        assert mod._get_type('blah') == 'string'



class TestGetFieldType(object):


    def test_get_field_type_basics(self):
        assert mod.get_field_type(None) == 'unknown'
        assert mod.get_field_type({}) == 'unknown'
        assert mod.get_field_type({'Texas': 4}) == 'string'
        assert mod.get_field_type({'1': 4}) == 'integer'
        assert mod.get_field_type({'n/a': 4, 'Texas':4}) == 'string'
        assert mod.get_field_type({'n/a': 4, '55':4}) == 'integer'
        assert mod.get_field_type({'n/a': 4, '55.5':4}) == 'float'
        assert mod.get_field_type({'n/a': 4, '':4}) == 'unknown'
        assert mod.get_field_type({'n/a': 4, '1310527566.7':4}) == 'float'
        assert mod.get_field_type({'4.3': 4, '1310527566.7':4}) == 'float'

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
        assert mod.get_field_type(test_data) == 'unknown'

    def test_get_field_type_mostly_strings(self):
        test_data = {'n/a':     1,
                     'blah':  999,
                     '0':       1,
                     '1.1':     1,
                     '2011-04': 1}
        assert mod.get_field_type(test_data) == 'string'
