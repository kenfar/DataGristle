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
import time
import subprocess

#might be necessary for testing later:
#import test_tools
#mod = test_tools.load_script('gristle_filter')



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))

    return suite


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w") 
 
    for i in range(record_cnt):
        fields = []
        fields.append(str(i))
        fields.append('A')
        fields.append('B')
        fields.append('C')
        if i // 10 == 0:
           fields.append('foo')
        else:
           fields.append('bar')
        #print delim.join(fields)
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn



class TestCommandLine(unittest.TestCase):

    def setUp(self):
        self.easy_fqfn     = generate_test_file(delim='|', record_cnt=100)
        self.empty_fqfn    = generate_test_file(delim='|', record_cnt=0)

    def tearDown(self):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)


    def test_easy_file(self):

        cmd = ['../gristle_filter',
               self.easy_fqfn, 
               '-c', '4 == foo']
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output = p.communicate()[0]
        p_recs   = p_output[:-1].split('\n')
   
        assert(len(p_recs) == 10)
        for rec in p_recs:
            fields = rec.split('|')
            assert(0 <= int(fields[0]) <= 9)
            assert(fields[1] == 'A')
            assert(fields[2] == 'B')
            assert(fields[3] == 'C')
            assert(fields[4] == 'foo')

        #assert(p_recs[0].strip().startswith('field_0'))
        #assert(p_recs[0].strip().endswith('9'))

        #assert(p_recs[1].strip().startswith('field_1'))
        #assert(p_recs[1].strip().endswith('A'))

        #assert(p_recs[2].strip().startswith('field_2'))
        #assert(p_recs[2].strip().endswith('B'))

        #assert(p_recs[3].strip().startswith('field_3'))
        #assert(p_recs[3].strip().endswith('C'))



    def test_empty_file(self):
        cmd = ['../gristle_filter'   ,
               self.empty_fqfn       ,
               '-c', '0 == foo'      ]
        p =  subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              close_fds=True)
        p_output  = p.communicate()[0]
        out_recs  = p_output[:-1].split('\n')
        if not out_recs:
            fail('produced output when input was empty')


    def test_multiple_empty_files(self):
        cmd = ['../gristle_filter'   ,
               self.empty_fqfn       ,
               self.empty_fqfn       ,
               '-d'  '|'             ,
               '-c', '0 == foo'      ]
        p =  subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              close_fds=True)
        p_output  = p.communicate()[0]
        out_recs  = p_output[:-1].split('\n')
        if not out_recs:
            fail('produced output when input was empty')


    def test_multiple_empty_and_full_files(self):
        cmd = ['../gristle_filter'   ,
               self.empty_fqfn       ,
               self.easy_fqfn        ,
               '-d'  '|'             ,
               '-c', '4 == bar'      ]
        p =  subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              close_fds=True)
        p_output  = p.communicate()[0]
        out_recs  = p_output[:-1].split('\n')
        assert(len(out_recs) == 90)
        if not out_recs:
            fail('produced output when input was empty')


    def test_multiple_full_files(self):
        cmd = ['../gristle_filter'   ,
               self.easy_fqfn        ,
               self.easy_fqfn        ,
               '-d'  '|'             ,
               '-c', '4 == bar'      ]
        p =  subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              close_fds=True)
        p_output  = p.communicate()[0]
        out_recs  = p_output[:-1].split('\n')
        assert(len(out_recs) == 180)
        if not out_recs:
            fail('produced output when input was empty')



    def test_empty_stdin(self):
        cmd = "cat /dev/null | ../gristle_filter -c '0 == foo' -d '|'"
        p   =  subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                shell=True).communicate()
        p_output  = p[0]
        out_recs  = p_output[:-1].split('\n')
        if not out_recs:
            fail('produced output when input was empty')




if __name__ == "__main__":
    unittest.main()

