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



class Test_get_case(unittest.TestCase):

    def setUp(self):
        self.test_u1 = ['AAA','BBB','CCC']
        self.test_u2 = ['AAA','BBB','CCC','$B']
        self.test_u2 = ['AAA','BBB','CCC','D`~!@#$%^&*()-+=[{]}']

        self.test_m1 = ['aaa','bbb','ccc']
        self.test_m2 = ['aaa','BBB','ccc']

        self.test_unk1 = ['111','222','333']
        self.test_unk2 = []

    def tearDown(self):
        pass
 
    def test_1(self):
        assert(mod.get_case('string', self.test_u1) == 'upper')
        assert(mod.get_case('string', self.test_u2) == 'upper')

        assert(mod.get_case('string', self.test_m1) == 'lower')
        assert(mod.get_case('string', self.test_m2) == 'mixed')

        assert(mod.get_case('string', self.test_unk1) == 'unknown')
        assert(mod.get_case('string', self.test_unk2) == 'unknown')


if __name__ == "__main__":
    unittest.main()



