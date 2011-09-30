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
import gristle_filter  as mod


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
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn



class TestCommandLine(unittest.TestCase):


    def test_easy_file(self):

        easy_fqfn     = generate_test_file(delim='|', record_cnt=100)
        cmd = ['../gristle_filter.py',
               '-f', easy_fqfn, 
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

        os.remove(easy_fqfn)


if __name__ == "__main__":
    unittest.main()

