#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest

sys.path.append('../')
import file_determinator  as mod


def suit():
    suite = unittest.TestSuit()
    suite.addTest(unittest.makeSuite(TestSomething))

    return suite



def generate_test_file1(delim, quoting, record_number):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w") 
    name_list = ['smith','jones','thompson','ritchie']
    role_list = ['pm','programmer','dba','sysadmin','qa','manager']
    proj_list = ['cads53','jefta','norma','us-cepa']
 
    for i in range(record_number):
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        if quoting is True:
           name = '"' + name + '"'
           role = '"' + role + '"'
           proj = '"' + proj + '"'
        record = '''%(i)s%(delim)s%(proj)s%(delim)s%(role)s%(delim)s%(name)s\n''' % locals()
        fp.write(record)

    fp.close()
    return fqfn



class TestQuotedCSV(unittest.TestCase):

    def setUp(self):
        self.record_number = 100
        self.delimiter     = '|'
        self.quoting       = True
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, self.record_number)
        self.MyTest     = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

    def tearDown(self):
        os.remove(self.test1_fqfn)

    def testMisc(self):
        assert(self.MyTest.record_number == self.record_number)
        assert(self.MyTest.field_number == 4)
        assert(self.MyTest.format_type == 'csv')
        assert(self.MyTest.dialect.delimiter == self.delimiter)
        assert(self.MyTest.csv_quoting == self.quoting)


class TestNonQuotedCSV(unittest.TestCase):

    def setUp(self):
        self.record_number = 100
        self.delimiter     = '|'
        self.quoting       = True
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, 
                          self.record_number)
        self.MyTest     = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

    def tearDown(self):
        os.remove(self.test1_fqfn)

    def testMisc(self):
        assert(self.MyTest.record_number == self.record_number)
        assert(self.MyTest.field_number == 4)
        assert(self.MyTest.format_type == 'csv')
        assert(self.MyTest.dialect.delimiter == self.delimiter)
        assert(self.MyTest.csv_quoting == self.quoting)


class TestInternals(unittest.TestCase):

    def setUp(self):
        self.record_number = 100
        self.delimiter     = '|'
        self.quoting       = False
        self.test1_fqfn = generate_test_file1(self.delimiter, self.quoting, 
                          self.record_number)
        self.MyTest     = mod.FileTyper(self.test1_fqfn)
        self.MyTest.analyze_file()

    def tearDown(self):
        os.remove(self.test1_fqfn)

    def testRecordNumber(self):
        assert(self.MyTest._count_records()
                == self.record_number)

    def testFormatType(self):
        assert(self.MyTest._get_format_type()
                == 'csv')


if __name__ == "__main__":
    #unittest.main(defaultTest="suite")
    unittest.main()

