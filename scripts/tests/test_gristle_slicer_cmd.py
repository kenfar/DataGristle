#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest
import time
import subprocess
from subprocess import PIPE, STDOUT, Popen

sys.path.append('../')
sys.path.append('../../')
import gristle_slicer  as mod


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


    def test_easy_file(self):

        easy_fqfn     = generate_test_file(delim='|', record_cnt=100)
        cmd = ['../gristle_slicer.py','-f', easy_fqfn, 
               '-c', ':',
               '-C', '3',
               '-r', '15:20',
               '-R', '18']
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output = p.communicate()[0]
        p_recs   = p_output[:-1].split('\n')
        for rec in p_recs:
            assert(rec.count('|') == 2)
            assert(rec.count('18') == 0 )
        assert(len(p_recs) == 4)

        os.remove(easy_fqfn)


    def test_small_file(self):
        easy_fqfn    = generate_test_file(delim='|', record_cnt=1)
        cmd = '../gristle_slicer.py -f %s -r 15:20' % easy_fqfn
        try:
          p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
          #records =  p.communicate()[0].split('\n')
          records =  p.communicate()[0]
          assert(len(records) == 0)
        except IOError:
           print 'IOError!'
        p.stdin.close()
        os.remove(easy_fqfn)


    def test_empty_file(self):
        easy_fqfn    = generate_test_file(delim='|', record_cnt=0)
        cmd = '../gristle_slicer.py -f %s -r 15:20' % easy_fqfn
        try:
          p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
          #records =  p.communicate()[0].split('\n')
          records =  p.communicate()[0]
          assert(len(records) == 0)
        except IOError:
           print 'IOError!'
        p.stdin.close()
        os.remove(easy_fqfn)


if __name__ == "__main__":
    unittest.main()

