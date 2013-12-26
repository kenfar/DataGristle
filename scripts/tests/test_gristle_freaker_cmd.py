#!/usr/bin/env python
""" 
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import random
import time
import fileinput
import subprocess
import envoy
import inspect
from pprint import pprint as pp

script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))


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



class TestCommandLine(object):

    def setup_class(self):

        self.easy_fqfn          = generate_test_file(delim='|', record_cnt=100)
        self.empty_fqfn         = generate_test_file(delim='|', record_cnt=0)
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestFreakerOut_')

    def teardown_class(self):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)

    def test_empty_file(self):
        cmd = '%s %s -o %s -c 0' % (os.path.join(script_path, 'gristle_freaker'),
                                    self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_empty_stdin_file(self):
        cmd = "cat %s | %s -d '|' -o %s -c 0" % (self.empty_fqfn,
                                                 os.path.join(script_path, 'gristle_freaker'),
                                                 self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_empty_multiple_files(self):
        cmd = "%s %s %s -d '|' -o %s -c 0" % (os.path.join(script_path, 'gristle_freaker'),
                                              self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_full_single_file(self):
        cmd = "%s %s -d '|' -o %s " % (os.path.join(script_path, 'gristle_freaker'),
                                              self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            field_list = rec[:-1].split('-')
            fields = []
            fields.append(int(field_list[0]))
            fields.append(field_list[1].strip())
            fields.append(field_list[2].strip())
            fields.append(field_list[3].strip())
            fields.append(int(field_list[4]))    # count field
            assert len(fields)    == 5
            assert fields[1]      == 'A'
            assert fields[2]      == 'B'
            assert fields[3]      == 'C'
            assert fields[4]      == 1           # always a '1' - all rows are unique
            out_recs.append(fields)

        fileinput.close()
        assert len(out_recs) == 100
        p.stdin.close()


    def test_full_multiple_files(self):
        cmd = "%s %s %s -d '|' -o %s -c 0" % (os.path.join(script_path, 'gristle_freaker'),
                                              self.easy_fqfn, self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 100
        p.stdin.close()


    def test_empty_and_full_multiple_files(self):
        cmd = "%s %s %s -d '|' -o %s -c 0" % (os.path.join(script_path, 'gristle_freaker'),
                                              self.empty_fqfn, self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 100
        p.stdin.close()



