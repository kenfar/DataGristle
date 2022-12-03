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
from typing import Any, Dict

import datagristle.field_type  as mod



class TestIsInteger(object):

    def test_is_integer_basics(self):
        assert mod.is_integer('3')
        assert mod.is_integer('-3')
        assert mod.is_integer(3)
        assert mod.is_integer(-3)
        assert mod.is_integer(3.0)        is False
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
        assert mod.is_float(44.0) is True
        assert mod.is_float(3) is False
        assert mod.is_float(0.0) is True
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



class TestFieldType(object):

    def runner(self, value):
        field_type = mod.FieldType([(value, 1)])
        return field_type.get_field_type()

    def multi_runner(self, field_freq: Dict[Any, int]):
        field_type = mod.FieldType(field_freq)
        return field_type.get_field_type()


    def test_misc(self):
        assert self.runner('n/a') == 'unknown'
        assert self.runner('UNK') == 'unknown'
        assert self.runner('unk') == 'unknown'
        assert self.runner(' ') == 'unknown'
        assert self.runner('') == 'unknown'
        assert self.runner('0') == 'integer'
        assert self.runner('1') == 'integer'
        assert self.runner('-1') == 'integer'
        assert self.runner('+1') == 'integer'
        assert self.runner('1.1') == 'float'
        assert self.runner('blah') == 'string'

    def test_get_field_type_basics(self):
        assert self.multi_runner([]) == 'unknown'
        assert self.multi_runner([('Texas', 4)]) == 'string'
        assert self.multi_runner([('1', 4)]) == 'integer'
        assert self.multi_runner([('n/a',4), ('Texas',4)]) == 'string'
        assert self.multi_runner([('n/a',4), ('55',4)]) == 'integer'
        assert self.multi_runner([('n/a', 4), ('55.5',4)]) == 'float'
        assert self.multi_runner([('n/a', 4), ('',4)]) == 'unknown'
        assert self.multi_runner([('n/a', 4), ('1310527566.7',4)]) == 'float'
        assert self.multi_runner([('4.3', 4), ('1310527566.7',4)]) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     '1.1':   4}
        assert self.multi_runner(test_data.items()) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     'blah':  4}
        assert self.multi_runner(test_data.items()) == 'unknown'

        test_data = {'n/a':   3,
                     'blah':  2,
                     '0':     2,
                     '1.1':   4}
        assert self.multi_runner(test_data.items()) == 'unknown'

    def test_get_field_type_mostly_strings(self):
        test_data = {'n/a':     1,
                     'blah':  999,
                     '0':       1,
                     '1.1':     1,
                     '2011-04': 1}
        assert self.multi_runner(test_data.items()) == 'string'

    def test_integers(self):
        assert self.runner("0") == 'integer'
        assert self.runner("-4") == 'integer'
        assert self.runner("2009 ") == 'integer'
        assert self.runner("2009 ") == 'integer'
        assert self.runner("2009") == 'integer'
        assert self.runner("200910") == 'integer'
        assert self.runner("20090206") == 'integer'

    def test_floats(self):
        assert self.runner("-4.7") == 'float'
        assert self.runner("1172969203.1") == 'float'

    def test_strings(self):
        assert self.runner("blah") == 'string'
        assert self.runner("blah") == 'string'
        assert self.runner("2009-10") == 'string'

    def test_unsupported_periods(self):
        assert self.runner("2009-10-06-18.10") == 'string'
        assert self.runner("2009-10-06-03.02.01") == 'string'

    def test_dates(self):
        assert self.runner("10/26/09") == 'timestamp'
        assert self.runner("10-26-09") == 'timestamp'
        assert self.runner("26/10/09") == 'timestamp'
        assert self.runner("26-10-09") == 'timestamp'
        assert self.runner("10/26/2009") == 'timestamp'
        assert self.runner("10-26-2009") == 'timestamp'
        assert self.runner("26/10/2009") == 'timestamp'
        assert self.runner("26-10-2009") == 'timestamp'

    def test_month_names(self):
        assert self.runner("Feb 13,2009") == 'timestamp'
        assert self.runner("Feb 13, 2009") == 'timestamp'
        assert self.runner("February 13,2009") == 'timestamp'
        assert self.runner("February 13, 2009") == 'timestamp'

    def test_iso8601(self):
        assert self.runner("2009-10-06") == 'timestamp'
        assert self.runner("2009-10-06T18:10") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01.01") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01.012") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01.01234") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01.012345") == 'timestamp'

    def test_non_iso8601_timestamps(self):
        assert self.runner("2009-10-06 18") == 'timestamp'
        assert self.runner("2009-10-06-18") == 'timestamp'

        assert self.runner("2009-10-06 18:10") == 'timestamp'
        assert self.runner("2009-10-06-18:10")  == 'timestamp'

        assert self.runner("2009-10-06 03:02:01") == 'timestamp'
        assert self.runner("2009-10-06-03:02:01") == 'timestamp'

        assert self.runner("2009-10-06-03:02:01.01") == 'timestamp'
        assert self.runner("2009-10-06 03:02:01.01234") == 'timestamp'
        assert self.runner("2009-10-06-03:02:01.01234") == 'timestamp'

        assert self.runner("2009-10-06D18:10") == 'string'

    def test_iso8601_with_timezone_z(self):
        assert self.runner("2009-10-06T03:02:01.01234Z") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01Z") == 'timestamp'
        assert self.runner("2009-10-06T03:02Z") == 'timestamp'

    def test_iso8601_with_timezone_plus(self):
        assert self.runner("2009-10-06T03:02:01.01234+0700") == 'timestamp'
        assert self.runner("2009-10-06T03:02:01+0700") == 'timestamp'
        assert self.runner("2009-10-06T03:02+0700") == 'timestamp'

    def test_timezone_with_timezone_dash(self):
        assert self.runner("2009-10-06T03:02:01.01234-0700") == 'timestamp'
        assert self.runner("2009-10-06T03:02-0700") == 'timestamp'



    def test_get_field_type_basicsII(self):
        assert self.multi_runner({}) == 'unknown'
        #assert self.multi_runner({'Texas': 4}) == 'string'
        #assert self.multi_runner({'1': 4}) == 'integer'
        #assert self.multi_runner({'n/a': 4, 'Texas':4}) == 'string'
        #assert self.multi_runner({'n/a': 4, '55':4}) == 'integer'
        #assert self.multi_runner({'n/a': 4, '55.5':4}) == 'float'
        #assert self.multi_runner({'n/a': 4, '':4}) == 'unknown'
        #assert self.multi_runner({'n/a': 4, '1310527566.7':4}) == 'float'
        #assert self.multi_runner({'4.3': 4, '1310527566.7':4}) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     '1.1':   4}
        assert self.multi_runner(test_data.items()) == 'float'

        test_data = {'n/a':   3,
                     '0':     2,
                     'blah':  4}
        assert self.multi_runner(test_data.items()) == 'unknown'

        test_data = {'n/a':   3,
                     'blah':  2,
                     '0':     2,
                     '1.1':   4}
        assert self.multi_runner(test_data.items()) == 'unknown'

    def test_get_field_type_mostly_strings_b(self):
        test_data = {'n/a':     1,
                     'blah':  999,
                     '0':       1,
                     '1.1':     1,
                     '2011-04': 1}
        assert self.multi_runner(test_data.items()) == 'string'
