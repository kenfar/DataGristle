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
import gristle_diff  as mod


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommandLine))

    return suite



def generate_test_file(delim, rec_list):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w") 
 
    for rec in rec_list:
        fp.write(delim.join(rec)+'\n')

    fp.close()
    return fqfn



class TestCommandLine(unittest.TestCase):


    def test_easy_files(self):
        """ Objective of this test to is to demonstrate correct processing
            for a pair of simple files.
        """

        file1_recs = [ ['Alabama','8','18'],
                       ['Alaska','6','16'],
                       ['Arizona','4','14'],
                       ['Arkansas','2','12'] ]
        file1    = generate_test_file('|', file1_recs)

        file2_recs = [ ['Alabama','8','18'],
                       ['Arizona','4','1a'],
                       ['Arkansas','2a','12'],
                       ['Wisconsin','13a','45b'] ]
        file2    = generate_test_file('|', file2_recs)

        cmd = ['../gristle_diff.py',
               '-1', file1,
               '-2', file2,
               '-k', '0',
               '-c', '1' ]
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             close_fds=True)
        p_output = p.communicate()[0]
        p_recs   = p_output[:-1].split('\n')
  
        for rec in p_recs:
            fields = rec.split(':')
            if fields[0].strip().startswith('In file1'):
                assert(fields[1].strip() == 'Alaska')
            if fields[0].strip().startswith('In file2'):
                assert(fields[1].strip() == 'Wisconsin')
            if fields[0].strip().startswith('In both'):
                assert(fields[1].strip() == 'Arkansas')

        os.remove(file1)
        os.remove(file2)

    def test_empty_files(self):
        """ Test behavior with one or both files empty
            TBD
        """
        pass

    def test_multi_column(self):
        """ Tests ability to specify multiple key or comparison columns
            TBD
        """
        pass

    def test_maxsize(self):
        """ Tests with files greater than maxsize and tests overriding of maxsize
            TBD
        """
        pass

    def test_dialect_overrides(self):
        """ Tests hasheader, delimiter, and recdelimiter args
            TBD
        """
        pass

    def test_counts(self):
        """ diff cmdline: Tests counts
            TBD
        """
        pass




if __name__ == "__main__":
    unittest.main()

