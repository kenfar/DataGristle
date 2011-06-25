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



class TestTypes(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_integer(self):
        assert(mod.is_integer('3')         is True)
        assert(mod.is_integer('-3')        is True)
        assert(mod.is_integer(3)           is True)
        assert(mod.is_integer(-3)          is True)
        assert(mod.is_integer('b')         is False)
        assert(mod.is_integer('')          is False)
        assert(mod.is_integer(' ')         is False)
        assert(mod.is_integer('$3')        is False)
        assert(mod.is_integer('4,333.22')  is False)
        assert(mod.is_integer('33.22')     is False)
        assert(mod.is_integer(3.3)         is False)
        assert(mod.is_integer(None)        is False)

    def test_is_float(self):
        assert(mod.is_float('33.22')     is True)
        assert(mod.is_float(44.55)       is True)
        assert(mod.is_float(3)           is False)
        assert(mod.is_float(0.0)         is False)
        assert(mod.is_float(0)           is False)
        assert(mod.is_float('b')         is False)
        assert(mod.is_float('')          is False)
        assert(mod.is_float(' ')         is False)
        assert(mod.is_float('$3')        is False)
        assert(mod.is_float('4,333.22')  is False)
        assert(mod.is_float('3')         is False)
        assert(mod.is_float('-3')        is False)
        assert(mod.is_float(None)        is False)

    def test_is_string(self):
        assert(mod.is_string('b')         is True)
        assert(mod.is_string('')          is True)
        assert(mod.is_string(' ')         is True)
        assert(mod.is_string('$3')        is True)
        assert(mod.is_string('4,333.22')  is True)
        assert(mod.is_string('33.22')     is False)
        assert(mod.is_string('3')         is False)
        assert(mod.is_string('-3')        is False)
        assert(mod.is_string(3)           is False)
        assert(mod.is_string(3.3)         is False)
        assert(mod.is_string(None)        is False)

    def test_is_unknown_value(self):
        assert(mod.is_unknown_value('')          is True)
        assert(mod.is_unknown_value(' ')         is True)
        assert(mod.is_unknown_value('na')        is True)
        assert(mod.is_unknown_value('NA')        is True)
        assert(mod.is_unknown_value('n/a')       is True)
        assert(mod.is_unknown_value('N/A')       is True)
        assert(mod.is_unknown_value('unk')       is True)
        assert(mod.is_unknown_value('unknown')   is True)
        assert(mod.is_unknown_value('b')         is False)
        assert(mod.is_unknown_value('$3')        is False)
        assert(mod.is_unknown_value('4,333.22')  is False)
        assert(mod.is_unknown_value('33.22')     is False)
        assert(mod.is_unknown_value('3')         is False)
        assert(mod.is_unknown_value('-3')        is False)
        assert(mod.is_unknown_value(3)           is False)
        assert(mod.is_unknown_value(3.3)         is False)
        assert(mod.is_unknown_value(None)        is False)



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

    def test_emptiness(self):
        assert(mod.get_max('string', self.empty_dict) is None)
        assert(mod.get_max('string', self.empty_list) is None)
        assert(mod.get_min('string', self.empty_dict) is None)
        assert(mod.get_min('string', self.empty_list) is None)

    def test_easy_dict(self):
        assert(mod.get_max('string', self.easy_dict)  == 'Wyoming')
        assert(mod.get_min('string', self.easy_dict)  == 'Nevada')

    def test_easy_list(self):
        assert(mod.get_max('string', self.easy_list)  == 'Wyoming')
        assert(mod.get_min('string', self.easy_list)  == 'Nevada')

    def test_unknowns(self):
        assert(mod.get_max('string', self.unk_list)  == 'Texas')
        assert(mod.get_max('string', self.unk_dict)  == 'Texas')
        assert(mod.get_min('string', self.unk_dict)  == 'Nevada')
        assert(mod.get_min('string', self.unk_list)  == 'Nevada')

    def test_mins(self):
        assert(mod.get_min('integer', self.num_dict)  == '9')



class TestGetMedian(unittest.TestCase):

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
    def tearDown(self):
        pass

    def test_emptiness(self):
        assert(mod.get_median(self.empty_dict_1) is None)
        assert(mod.get_median(self.empty_list_1) is None)
        assert(mod.get_median(self.empty_dict_2) is None)
        assert(mod.get_median(self.empty_list_2) is None)

    def test_easy_list(self):
        assert(mod.get_median(self.easy_list)  == 4)

    def test_small_sets(self):
        assert(mod.get_median(self.small_list_1)  == 8)
        assert(mod.get_median(self.small_list_2)  == 4.5)
        assert(mod.get_median(self.small_list_3)  == 4)



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



class TestCase(unittest.TestCase):

    def setUp(self):
        self.empty_dict   = {}
        self.mixedstring_1 = {'Wyoming': 3,
                             'Nevada':  2,
                             'Texas':   4}
        self.mixedstring_2 = {'wyoming': 3,
                             'nevada':  2,
                             'Texas':   4}
        self.lowerstring_1 = {'wyoming': 3,
                             'nevada':  2,
                             'texas':   4}
        self.lowerstring_2 = {'wyoming': 3,
                             'unk':      2,
                             'NA':       2,
                             'texas':    4}
        self.upperstring_1 = {'WYOMING': 3,
                              'NEVADA':  2,
                              'TEXAS':   4}
        self.upperstring_2 = {'WYOMING': 3,
                              'NEVADA':  2,
                              '':        4,
                              'n/a':     4}
        self.nonstring_1  = {'33':4, 'Wyoming': 3}
        self.mixedlist_1  = ['Wyoming','Utah']
        self.lowerlist_1  = ['wyoming','utah','UNK']

    def tearDown(self):
        pass

    def test_empty_dict(self):
        assert(mod.get_case('string', self.empty_dict) == 'unknown')

    def test_non_strings(self):
        assert(mod.get_case('integer', self.nonstring_1) == 'n/a')
        assert(mod.get_case('float', self.nonstring_1) == 'n/a')
        assert(mod.get_case('date', self.nonstring_1) == 'n/a')

    def test_mixed_strings(self):
        assert(mod.get_case('string', self.mixedstring_1) == 'mixed')
        assert(mod.get_case('string', self.mixedstring_2) == 'mixed')

    def test_lower_strings(self):
        assert(mod.get_case('string', self.lowerstring_1) == 'lower')
        assert(mod.get_case('string', self.lowerstring_2) == 'lower')

    def test_upper_strings(self):
        assert(mod.get_case('string', self.upperstring_1) == 'upper')
        assert(mod.get_case('string', self.upperstring_2) == 'upper')

    def test_lower_list(self):
        assert(mod.get_case('string', self.mixedlist_1) == 'mixed')
        assert(mod.get_case('string', self.lowerlist_1) == 'lower')



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
        fp3.write(data_rec)
        fp3.close()

    def tearDown(self):
        os.remove(self.header_fqfn)
        os.remove(self.headless_fqfn)
        os.remove(self.empty_fqfn)

    def test_header(self):
        assert(mod.get_field_names(self.header_fqfn,1, True, ',') == 'phone')

    def test_headless(self):
        assert(mod.get_field_names(self.headless_fqfn,1, False, ',') == 'field_num_1')

    #def test_empty(self):
    #don't yet have this working yet
    #    assert(mod.get_field_names(self.empty_fqfn,1, True, ',') is None )



class TestGetType(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1(self):
        assert(mod.get_type('n/a')  == 'unknown')
        assert(mod.get_type('UNK')  == 'unknown')
        assert(mod.get_type('unk')  == 'unknown')
        assert(mod.get_type(' ')    == 'unknown')
        assert(mod.get_type('')     == 'unknown')
        assert(mod.get_type('0')    == 'integer')
        assert(mod.get_type('1')    == 'integer')
        assert(mod.get_type('-1')   == 'integer')
        assert(mod.get_type('+1')   == 'integer')
        assert(mod.get_type('1.1')  == 'float')
        assert(mod.get_type('blah') == 'string')

class TestGetFieldType(unittest.TestCase):

    def setUp(self):
        self.type_0a = []
        self.type_0b = {}
        self.type_1a = {'Texas':   4}
        self.type_1b = ['1']
        self.type_2a = ['n/a', 'Texas']
        self.type_2b = ['n/a', '55']
        self.type_2c = ['n/a', '55.5']
        self.type_2d = ['n/a', '']
        self.type_3a = {'n/a':   3,
                        '0':     2,
                        '1.1':   4}
        self.type_3b = {'n/a':   3,
                        '0':     2,
                        'blah':  4}
        self.type_4 = {'n/a':   3,
                       'blah':  2,
                       '0':     2,
                       '1.1':   4}


    def tearDown(self):
        pass

    def test_1(self):
        assert(mod.get_field_type(self.type_0a) == 'unknown')
        assert(mod.get_field_type(self.type_0b) == 'unknown')
        assert(mod.get_field_type(self.type_1a) == 'string')
        assert(mod.get_field_type(self.type_1b) == 'integer')
        assert(mod.get_field_type(self.type_2a) == 'string')
        assert(mod.get_field_type(self.type_2b) == 'integer')
        assert(mod.get_field_type(self.type_2c) == 'float')
        assert(mod.get_field_type(self.type_2d) == 'unknown')
        assert(mod.get_field_type(self.type_3a) == 'float')
        #assert(mod.get_field_type(self.type_3b) == 'unknown')
        #assert(mod.get_field_type(self.type_4)  == 'unknown')


if __name__ == "__main__":
    unittest.main()



