#!/usr/bin/env python
""" To do:
      1.  Add testing for stdout - but can be hard because it has interactive prompting.
      2.  Add testing for a recnum > last record in the file

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

import sys
import os
import tempfile
import random
import unittest
import time
import fileinput
import subprocess
import imp
import envoy

script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm      = os.path.join(script_path, 'gristle_viewer')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))
    unittest.TextTestRunner(verbosity=2).run(suite)

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
        self.empty_fqfn          = generate_test_file(delim='|', record_cnt=0)
        (dummy, self.out_fqfn)   = tempfile.mkstemp(prefix='ViewerTestOut_') 

    def tearDown(self):
        os.remove(self.in_fqfn)
        os.remove(self.out_fqfn)

    def test_easy_file(self):

        cmd = '%s %s -r 10 -o %s' % (fq_pgm, self.in_fqfn, self.out_fqfn)
        r   = envoy.run(cmd)
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec)

        self.assertEqual(len(p_recs), 4)

        self.assertTrue(p_recs[0].strip().startswith('field_0'))
        self.assertTrue(p_recs[0].strip().endswith('10'))

        self.assertTrue(p_recs[1].strip().startswith('field_1'))
        self.assertTrue(p_recs[1].strip().endswith('A'))

        self.assertTrue(p_recs[2].strip().startswith('field_2'))
        self.assertTrue(p_recs[2].strip().endswith('B'))

        self.assertTrue(p_recs[3].strip().startswith('field_3'))
        self.assertTrue(p_recs[3].strip().endswith('C'))


    def test_bad_recnum(self):
        """ Shows that the program when given a recnum that doesn't exist will 
            write no rows to the output file and print only a comment to stdout

            To do:
                - check for a negative number
                - check for return code
        """

        p_outrecs = []
        cmd = '%s %s -r 999 -o %s' % (fq_pgm, self.in_fqfn, self.out_fqfn)
        r   = envoy.run(cmd)
        for rec in fileinput.input(self.out_fqfn):
            p_outrecs.append(rec)

        self.assertTrue('No record found' in r.std_out)
        self.assertEqual(len(p_outrecs), 0)


    def test_empty_file(self):
        cmd = "%s %s -o %s -r 999 " % (fq_pgm, self.empty_fqfn, self.out_fqfn )
        r   = envoy.run(cmd)
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        self.assertEqual(len(out_recs), 0)


    def test_full_multiple_files(self):
        cmd = "%s %s %s -o %s -r 10 -d'|'" % (fq_pgm, self.in_fqfn, self.in_fqfn, self.out_fqfn)
        r   = envoy.run(cmd)
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)

        self.assertTrue(len(out_recs) == 4)
        self.assertTrue(out_recs[0].strip().startswith('field_0'))
        self.assertTrue(out_recs[0].strip().endswith('10'))


    def test_full_multiple_empty_files(self):
        cmd = "%s %s %s -o %s -r 10 -d'|'" % (fq_pgm, self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        r   = envoy.run(cmd)
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)

        self.assertTrue(len(out_recs) == 0)


    def dtest_full_multiple_empty_and_full_files(self):
        cmd = "%s %s %s -o %s -r 10 -d'|'" % (fq_pgm, self.empty_fqfn, self.in_fqfn, self.out_fqfn)
        r   = envoy.run(cmd)
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)

        self.assertTrue(len(out_recs) == 4)
        self.assertTrue(out_recs[0].strip().startswith('field_0'))
        self.assertTrue(out_recs[0].strip().endswith('10'))



if __name__ == "__main__":
    unittest.main(suite())

