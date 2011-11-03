#!/usr/bin/env python
#------------------------------------------------------------------------------
#  To do:
#  1.  test with multiple input files
#
#  See the file "LICENSE" for the full license governing this code. 
#------------------------------------------------------------------------------

import sys
import os
import tempfile
import random
import unittest
import time
import fileinput
import subprocess

sys.path.append('../')
sys.path.append('../../')
import gristle_slicer  as mod


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))

    return suite


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicerIn_')
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
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestSliceOut_')

    def tearDown(self): 
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)


    def test_easy_file(self):

        cmd = ['../gristle_slicer.py',
               self.easy_fqfn, 
               '-o', self.out_fqfn,
               '-c', ':',
               '-C', '3',
               '-r', '15:20',
               '-R', '18' ]

        p = subprocess.Popen(cmd, 
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output      = p.communicate()[0]
        stdout_recs   = p_output[:-1].split('\n')
        out_recs      = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)

        for rec in out_recs:
            assert(rec.count('|') == 2)
            assert(rec.count('18') == 0 )
        assert(len(out_recs) == 4)



    def test_asking_for_too_much(self):
        cmd = '../gristle_slicer.py  %s -o %s -r 10:200' % (self.easy_fqfn, self.out_fqfn)
        try:
            p =  subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
            records   =  p.communicate()[0]
            out_recs  = []
            for rec in fileinput.input(self.out_fqfn):
                out_recs.append(rec)
            assert(len(out_recs) == 90)  # gets everything from 10 to 100 == 90
        except IOError:
           print 'IOError!'
        p.stdin.close()



    def test_empty_file(self):
        """ Should show proper handling of an empty file.   
        """
        cmd = '../gristle_slicer.py %s -o %s -r 15:20' % (self.empty_fqfn, self.out_fqfn)
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


if __name__ == "__main__":
    unittest.main()

