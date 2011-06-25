#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest

sys.path.append('../')
import field_determinator  as mod


def suit():
    suite = unittest.TestSuit()
    suite.addTest(unittest.makeSuite(TestSomething))

    return suite



class TestDatetimeChecker(unittest.TestCase):

    def setUp(self):
        self.MyCheck = mod.DatetimeChecker()

    def tearDown(self):
        pass

    def runner(self, date):
        result, scope, pattern = self.MyCheck.datetime_check(date)
        return result, scope
 
    def test_datetime_basic_check(self):
        assert(self.MyCheck.datetime_basic_check("blah") is False)
        assert(self.MyCheck.datetime_basic_check("blah2foop") is False)
        assert(self.MyCheck.datetime_basic_check("$100") is False)
        assert(self.MyCheck.datetime_basic_check("") is False)
        #assert(self.MyCheck.datetime_basic_check(None) is False)

        assert(self.MyCheck.datetime_basic_check("2011-03-11") is True)
        assert(self.MyCheck.datetime_basic_check("2011-03-11 03:02:01.99") is True)
        assert(self.MyCheck.datetime_basic_check("2011") is True)

    def test_DatetimeChecker(self):
        assert(self.runner("0")         == (False, None))
        assert(self.runner("-4")        == (False, None))
        assert(self.runner("-4.7")      == (False, None))
        assert(self.runner("blah")      == (False, None))

        assert(self.runner("1172969203.1")   == (True, 'second'))

        assert(self.runner("2009")   == (True, 'year'))

        assert(self.runner("200910") == (True, 'month'))
        assert(self.runner("2009-10") == (True, 'month'))

        assert(self.runner("20090206")     == (True, 'day'))
        assert(self.runner("2009-10-06") == (True, 'day'))
        assert(self.runner("10/26/09")   == (True, 'day'))
        assert(self.runner("10-26-09")   == (True, 'day'))
        assert(self.runner("26/10/09")   == (True, 'day'))
        assert(self.runner("26-10-09")   == (True, 'day'))
        assert(self.runner("10/26/2009") == (True, 'day'))
        assert(self.runner("10-26-2009") == (True, 'day'))
        assert(self.runner("26/10/2009") == (True, 'day'))
        assert(self.runner("26-10-2009") == (True, 'day'))
        assert(self.runner("Feb 13,2009") == (True, 'day'))
        assert(self.runner("Feb 13, 2009") == (True, 'day'))
        assert(self.runner("February 13,2009") == (True, 'day'))
        assert(self.runner("February 13, 2009") == (True, 'day'))
        assert(self.runner("2009-10-06 18") == (True, 'hour'))
        assert(self.runner("2009-10-06-18") == (True, 'hour'))
        assert(self.runner("2009-10-06 18:10") == (True, 'minute'))
        assert(self.runner("2009-10-06-18.10") == (True, 'minute'))
        assert(self.runner("2009-10-06 03:02:01") == (True, 'second'))
        assert(self.runner("2009-10-06 00:00:00") == (True, 'second'))
        assert(self.runner("2009-10-06 03:02:01.01") == (True, 'microsecond'))
        assert(self.runner("2009-10-06 03:02:01.01234") == (True, 'microsecond'))
        assert(self.runner("2009-10-06-18") == (True, 'hour'))
        assert(self.runner("2009-10-06-03.02.01") == (True, 'second'))

        assert(self.runner("blah")  == (False, None))
        assert(self.runner("2009 ") == (False, None))
        assert(self.runner("2009 ") == (False, None))




if __name__ == "__main__":
    unittest.main()



