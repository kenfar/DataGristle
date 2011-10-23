#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest
import time
import subprocess

sys.path.append('../')
sys.path.append('../../')
import gristle_file_converter  as mod


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
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn



class TestCommandLine(unittest.TestCase):


    def test_input_and_output_del(self):

        easy_fqfn     = generate_test_file(delim='|', record_cnt=100)
        cmd = ['../gristle_file_converter.py','-f', easy_fqfn, 
               '-d', '|',
               '-D', ',']
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output = p.communicate()[0]
        p_recs   = p_output[:-1].split('\n')
        for rec in p_recs:
            assert(rec.count(',') == 3)
        assert(len(p_recs) == 100)

        os.remove(easy_fqfn)


    def test_output_del_only(self):
        easy_fqfn    = generate_test_file(delim='|', record_cnt=100)
        cmd = "../gristle_file_converter.py -f %s -D ',' " % easy_fqfn
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)

        p_output = p.communicate()[0]
        p_recs   = p_output[:-1].split('\n')
        for rec in p_recs:
            assert(rec.count(',') == 3)
        assert(len(p_recs) == 100)

        os.remove(easy_fqfn)



if __name__ == "__main__":
    unittest.main()

