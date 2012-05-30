#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

import sys
import os
import tempfile
import random
import unittest
import subprocess
from subprocess import PIPE, STDOUT, Popen

sys.path.append('../')
sys.path.append('../../')
import gristle_slicer  as mod


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_spec_evaluator))
    suite.addTest(unittest.makeSuite(Test_process_cols))

    return suite


class Test_spec_evaluator(unittest.TestCase):

    def setUp(self):
        self.spec1   = ['5','7','9']
        self.value1  = '13'
        self.result1 = False

        self.spec2   = ['5','7','9']
        self.value2  = '7'
        self.result2 = True

        self.spec3   = [':']
        self.value3  = '7'
        self.result3 = True

        self.spec4   = ['2:']
        self.value4  = '7'
        self.result4 = True

        self.spec5   = [':8']
        self.value5  = '4'
        self.result5 = True

        self.spec6   = ['2:4']
        self.value6  = '7'
        self.result6 = False

        self.spec7   = ['2:4']
        self.value7  = '3'
        self.result7 = True

        self.spec8   = ['19','2:4','22']
        self.value8  = '3'
        self.result8 = True

        self.spec9   = ['19','2:4','22']
        self.value9  = '4'
        self.result9 = False


    def test_slicer_a01(self):
        assert(mod.spec_evaluator(self.value1, self.spec1) == self.result1)
        assert(mod.spec_evaluator(self.value2, self.spec2) == self.result2)
        assert(mod.spec_evaluator(self.value3, self.spec3) == self.result3)
        assert(mod.spec_evaluator(self.value4, self.spec4) == self.result4)
        assert(mod.spec_evaluator(self.value5, self.spec5) == self.result5)
        assert(mod.spec_evaluator(self.value6, self.spec6) == self.result6)
        assert(mod.spec_evaluator(self.value7, self.spec7) == self.result7)
        assert(mod.spec_evaluator(self.value8, self.spec8) == self.result8)
        assert(mod.spec_evaluator(self.value9, self.spec9) == self.result9)



class Test_process_cols(unittest.TestCase):

    def setUp(self):

        self.rec_cnt1      = '101'
        self.i_rec_spec1   = ['9:13', '44', '78', '80:140']
        self.e_rec_spec1   = ['89']
        self.cols1         = ['a','b','c','d','e','f','g']
        self.i_col_spec1   = ['1']
        self.e_col_spec1   = ['89']
        self.result1       = ['b']

    def test_slicer_a01(self):
        assert(mod.process_cols(self.rec_cnt1, 
                                self.i_rec_spec1, self.e_rec_spec1,
                                self.cols1,
                                self.i_col_spec1, self.e_col_spec1) \
                        == self.result1)

    def test_slicer_a02(self):
        self.e_col_spec1 = []
        assert(mod.process_cols(self.rec_cnt1, 
                                self.i_rec_spec1, self.e_rec_spec1,
                                self.cols1,
                                self.i_col_spec1, self.e_col_spec1) \
                    == self.result1)

    def test_slicer_a03(self):
        self.e_rec_spec1 = []
        assert(mod.process_cols(self.rec_cnt1, 
                                self.i_rec_spec1, self.e_rec_spec1,
                                self.cols1,
                                self.i_col_spec1, self.e_col_spec1) \
                    == self.result1)

    def test_slicer_a04(self):
        self.e_rec_spec1 = ['101']
        assert(mod.process_cols(self.rec_cnt1, 
                                self.i_rec_spec1, self.e_rec_spec1,
                                self.cols1,
                                self.i_col_spec1, self.e_col_spec1) \
                    == None)



if __name__ == "__main__":
    unittest.main()




