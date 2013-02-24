#!/usr/bin/env python
""" To do:
     1.  test with multiple input files

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import random
import unittest
import time
import fileinput
import subprocess

#might be necessary for testing later:
#import test_tools; mod = test_tools.load_script('gristle_freaker')



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))

    return suite


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestFreakerIn_')
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

    def setUp(self):

        self.easy_fqfn          = generate_test_file(delim='|', record_cnt=100)
        self.empty_fqfn         = generate_test_file(delim='|', record_cnt=0)
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestFreakerOut_')

    def tearDown(self): 
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)

    def test_empty_file(self):
        cmd = '../gristle_freaker %s -o %s -c 0' % (self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        assert(len(out_recs) == 0)
        p.stdin.close()


    def test_empty_stdin_file(self):
        cmd = "cat %s | ../gristle_freaker -d '|' -o %s -c 0" % (self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        assert(len(out_recs) == 0)
        p.stdin.close()


    def test_empty_multiple_files(self):
        cmd = "../gristle_freaker %s %s -d '|' -o %s -c 0" % (self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        assert(len(out_recs) == 0)
        p.stdin.close()


    def test_full_multiple_files(self):
        cmd = "../gristle_freaker %s %s -d '|' -o %s -c 0" % (self.easy_fqfn, self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        assert(len(out_recs) == 100)
        p.stdin.close()


    def test_empty_and_full_multiple_files(self):
        cmd = "../gristle_freaker %s %s -d '|' -o %s -c 0" % (self.empty_fqfn, self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        assert(len(out_recs) == 100)
        p.stdin.close()




if __name__ == "__main__":
    unittest.main()

