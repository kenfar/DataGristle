#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest

sys.path.append('../')
import field_misc  as mod


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_get_case))
    suite.addTest(unittest.makeSuite(Test_get_field_freq))
    suite.addTest(unittest.makeSuite(TestGetFieldNames))
    suite.addTest(unittest.makeSuite(TestMinAndMax))

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
 
    def test_misc_a01(self):
        assert(mod.get_case('string', self.test_u1) == 'upper')
        assert(mod.get_case('string', self.test_u2) == 'upper')

        assert(mod.get_case('string', self.test_m1) == 'lower')
        assert(mod.get_case('string', self.test_m2) == 'mixed')

        assert(mod.get_case('string', self.test_unk1) == 'unknown')
        assert(mod.get_case('string', self.test_unk2) == 'unknown')


class Test_get_field_freq(unittest.TestCase):

    def setUp(self):
        (fd1, self.test1_fqfn) = tempfile.mkstemp()
        fp1 = os.fdopen(fd1,"w")
        for x in range(100):
           reca = 'a%d|a%d|a%d\n' % (x,x,x)
           fp1.write(reca)
           recb = 'b%d|b%d|b%d\n' % (x,x,x)
           fp1.write(recb)
        fp1.close()

    def tearDown(self):
        os.remove(self.test1_fqfn)

    def test_misc_b01_truncation(self):
        (freq, trunc_flag) = mod.get_field_freq(self.test1_fqfn, 
                                   field_number=0,
                                   has_header=False,
                                   field_delimiter='|',
                                   max_freq_size=4)
        assert(len(freq) == 4)
        assert(trunc_flag is True)

    def test_misc_b02(self):
        (freq, trunc_flag) = mod.get_field_freq(self.test1_fqfn, 
                                   field_number=0,
                                   has_header=False,
                                   field_delimiter='|')
        assert(len(freq) == 200)
        assert(trunc_flag is False)
                              


                              


class TestGetFieldNames(unittest.TestCase):

    def setUp(self):
        header_rec = 'name,phone,gender,age'
        data_rec = 'ralph,719-555-1212,m,39'

        (fd1, self.header_fqfn) = tempfile.mkstemp()
        fp1 = os.fdopen(fd1,"w")
        fp1.write(header_rec)
        fp1.write(data_rec)
        fp1.close()

        (fd2, self.headless_fqfn) = tempfile.mkstemp()
        fp2 = os.fdopen(fd2,"w")
        fp2.write(data_rec)
        fp2.close()

        (fd3, self.empty_fqfn) = tempfile.mkstemp()
        fp3 = os.fdopen(fd3,"w")
        fp3.close()

    def tearDown(self):
        os.remove(self.header_fqfn)
        os.remove(self.headless_fqfn)
        os.remove(self.empty_fqfn)

    def test_misc_c01_header(self):
        assert(mod.get_field_names(self.header_fqfn,1, True, ',') == 'phone')

    def test_misc_c02_headless(self):
        assert(mod.get_field_names(self.headless_fqfn,1, False, ',') == 'field_num_1')

    def test_misc_c03_empty(self):
        assert(mod.get_field_names(self.empty_fqfn,1, True, ',') is None )



class TestMinAndMax(unittest.TestCase):

    def setUp(self):
        self.empty_dict  = {}
        self.empty_list  = []
        self.easy_dict   = {'Wyoming': 3,
                            'Nevada':  2,
                            'Texas':   4}
        self.easy_list   = ['Wyoming',
                            'Nevada',
                            'Texas' ]
        self.unk_list    = ['UNK',
                            'unknown',
                            ' ',
                            'Nevada',
                            'Texas' ]
        self.unk_dict    = {'UNK':1    ,
                            'unknown':3,
                            ' ':99     ,
                            'Nevada':4 ,
                            'Texas': 4}
        self.num_dict    = {'9':1      ,
                            '202':3    ,
                            ' ':99     ,
                            '51':4     ,
                            '777':2    ,
                            '11':2 }
    def tearDown(self):
        pass

    def test_misc_d01_emptiness(self):
        assert(mod.get_max('string', self.empty_dict) is None)
        assert(mod.get_max('string', self.empty_list) is None)
        assert(mod.get_min('string', self.empty_dict) is None)
        assert(mod.get_min('string', self.empty_list) is None)

    def test_misc_d02_easy_dict(self):
        assert(mod.get_max('string', self.easy_dict)  == 'Wyoming')
        assert(mod.get_min('string', self.easy_dict)  == 'Nevada')

    def test_misc_d03_easy_list(self):
        assert(mod.get_max('string', self.easy_list)  == 'Wyoming')
        assert(mod.get_min('string', self.easy_list)  == 'Nevada')

    def test_misc_d04_unknowns(self):
        assert(mod.get_max('string', self.unk_list)  == 'Texas')
        assert(mod.get_max('string', self.unk_dict)  == 'Texas')
        assert(mod.get_min('string', self.unk_dict)  == 'Nevada')
        assert(mod.get_min('string', self.unk_list)  == 'Nevada')

    def test_misc_d05_mins(self):
        assert(mod.get_min('integer', self.num_dict)  == '9')





if __name__ == "__main__":
    unittest.main()




