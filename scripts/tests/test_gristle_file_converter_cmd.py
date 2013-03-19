#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""


import sys
import os
import tempfile
import random
import unittest
import time
import subprocess

script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))
    unittest.TextTestRunner(verbosity=2).run(suite)

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

    def setUp(self):
        self.easy_fqfn     = generate_test_file(delim='|', record_cnt=100)
        self.empty_fqfn    = generate_test_file(delim='|', record_cnt=0)

    def tearDown(self):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)

    def test_input_and_output_del(self):

        cmd = [os.path.join(script_path, 'gristle_file_converter'),
               self.easy_fqfn, 
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


    def test_output_del_only(self):
        cmd = "%s  %s -D ',' " % (os.path.join(script_path, 'gristle_file_converter'), self.easy_fqfn)
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


    def test_empty_file(self):
        cmd = "%s  %s -d'|' -D ',' " % (os.path.join(script_path, 'gristle_file_converter'),
                                        self.empty_fqfn)
        p =  subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              shell=True)
        p_output  = p.communicate()[0]
        out_recs  = p_output[:-1].split('\n')
        if not out_recs:
            self.fail('produced output when input was empty')


if __name__ == "__main__":
    unittest.main(suite())

