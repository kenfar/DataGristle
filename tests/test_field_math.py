#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest

sys.path.append('../lib')
import field_math  as mod


def suit():
    suite = unittest.TestSuit()
    suite.addTest(unittest.makeSuite(TestSomething))

    return suite




class DontTestGetMedian(unittest.TestCase):

    def setUp(self):
        self.empty_dict_1  = {}
        self.empty_dict_2  = {'blah':2}
        self.empty_list_1  = []
        self.empty_list_2  = ['blah']
        self.easy_dict   = {'8': 3,
                            '1': 2,
                            '4': 4}
        self.easy_list   = ['8',
                            '1',
                            '4' ]
        self.small_list_1 = ['8']
        self.small_list_2 = ['8','1']
        self.small_list_3 = ['8','1','4']
        self.unk_list    = ['UNK',
                            'unknown',
                            ' ',
                            '8',
                            '1' ]
        self.unk_dict    = {'UNK':1,
                            'unknown':3,
                            ' ':99,
                            '8':4,
                            '1':2 }
        self.med_dict_1  = {'1':1,
                            '2':1,
                            '3':1,
                            '4':1,
                            '100':99 }
    def tearDown(self):
        pass

    def dont_test_emptiness(self):
        assert(mod.get_median(self.empty_dict_1) is None)
        assert(mod.get_median(self.empty_list_1) is None)
        assert(mod.get_median(self.empty_dict_2) is None)
        assert(mod.get_median(self.empty_list_2) is None)

    def dont_test_easy_list(self):
        assert(mod.get_median(self.easy_list)  == 4)

    def dont_test_small_sets(self):
        assert(mod.get_median(self.small_list_1)  == 8)
        assert(mod.get_median(self.small_list_2)  == 4.5)
        assert(mod.get_median(self.small_list_3)  == 4)

    def dont_test_medium_sets(self):
        assert(mod.get_median(self.med_dict_1)  == 100)



class TestGetMean(unittest.TestCase):

    def setUp(self):
        self.empty_dict_1  = {}
        self.empty_dict_2  = {'blah':2}
        self.empty_list_1  = []
        self.empty_list_2  = ['blah']
        self.easy_dict   = {'8': 3,
                            '1': 2,
                            '3': 4}
        self.easy_list   = ['8',
                            '1',
                            '3' ]
        self.small_list_1 = ['8']
        self.small_list_2 = ['8','2']
        self.small_list_3 = ['8','1','3']
        self.unk_list    = ['UNK',
                            'unknown',
                            ' ',
                            '8',
                            '2' ]
        self.unk_dict    = {'UNK':1,
                            'unknown':3,
                            ' ':99,
                            '8':4,
                            '2':2 }
        self.med_dict_1  = {'10':4,
                            '100':86 }
    def tearDown(self):
        pass

    def test_emptiness(self):
        assert(mod.get_mean(self.empty_dict_1) is None)
        assert(mod.get_mean(self.empty_list_1) is None)
        assert(mod.get_mean(self.empty_dict_2) is None)
        assert(mod.get_mean(self.empty_list_2) is None)

    def test_easy_list(self):
        assert(mod.get_mean(self.easy_list)  == 4)

    def test_small_sets(self):
        assert(mod.get_mean(self.small_list_1)  == 8)
        assert(mod.get_mean(self.small_list_2)  == 5)
        assert(mod.get_mean(self.small_list_3)  == 4)

    def test_medium_sets(self):
        assert(mod.get_mean(self.med_dict_1)  == 96)


if __name__ == "__main__":
    unittest.main()



