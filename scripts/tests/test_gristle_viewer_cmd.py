#!/usr/bin/env python
#-------------------------------------------------------------------------------
#  
#  To do:
#  1.  Add testing for stdin & stdout - but stdout can be hard because it has 
#      interactive prompting.
#  2.  Add testing for a recnum > last record in the file
#
#  See the file "LICENSE" for the full license governing this code. 
#
#-------------------------------------------------------------------------------

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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))

    return suite


def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='ViewerTestIn_')
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
        self.in_fqfn             = generate_test_file(delim='|', record_cnt=100)
        (dummy, self.out_fqfn)   = tempfile.mkstemp(prefix='ViewerTestOut_') 

    def tearDown(self):
        os.remove(self.in_fqfn)
        os.remove(self.out_fqfn)

    def test_easy_file(self):

        cmd = ['../gristle_viewer.py',
               self.in_fqfn, 
               '-r', '10',
               '-o', self.out_fqfn ]
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output = p.communicate()[0]
        ###p_recs   = p_output[:-1].split('\n')   # leftover from when output was captured from stdout
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec)

        assert(len(p_recs) == 4)

        assert(p_recs[0].strip().startswith('field_0'))
        assert(p_recs[0].strip().endswith('10'))

        assert(p_recs[1].strip().startswith('field_1'))
        assert(p_recs[1].strip().endswith('A'))

        assert(p_recs[2].strip().startswith('field_2'))
        assert(p_recs[2].strip().endswith('B'))

        assert(p_recs[3].strip().startswith('field_3'))
        assert(p_recs[3].strip().endswith('C'))


    def test_bad_recnum(self):
        """ Shows that the program when given a recnum that doesn't exist will 
            write no rows to the output file and print only a comment to stdout

            To do:
                - check for a negative number
                - check for return code
        """

        cmd = ['../gristle_viewer.py',
               self.in_fqfn, 
               '-r', '999',
               '-o', self.out_fqfn ]
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output   = p.communicate()[0]
        p_stdout   = p_output[:-1].split('\n')   # leftover from when output was captured from stdout
        p_outrecs  = []
        for rec in fileinput.input(self.out_fqfn):
            p_outrecs.append(rec)
        
        assert(len(p_stdout) == 1)
        assert(p_stdout[0] == 'No record found')

        assert(len(p_outrecs) == 0)


if __name__ == "__main__":
    unittest.main()

