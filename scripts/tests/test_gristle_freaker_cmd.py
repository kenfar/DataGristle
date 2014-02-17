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

import test_tools



def generate_test_file(delim, record_cnt, name='generic'):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestFreakerIn_%s_' % name)
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

    def setup_method(self, method):

        self.easy_fqfn          = generate_test_file(delim='|',
                                                     record_cnt=100,
                                                     name='easy')
        self.empty_fqfn         = generate_test_file(delim='|',
                                                     record_cnt=0,
                                                     name='empty')
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestFreakerOut_')

    def teardown_method(self, method):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestFreaker'))

    def test_empty_file(self):
        cmd = '%s %s -o %s -c 0' % (os.path.join(script_path, 'gristle_freaker'),
                                    self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        #for record in records.split('\n'):
        #    print record
        #print 'returncode:'
        #print p.returncode
        assert os.strerror(p.returncode).lower() == 'no data available'
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_empty_stdin_file(self):
        cmd = "cat %s | %s -d '|' -o %s -c 0" % (self.empty_fqfn, os.path.join(script_path, 'gristle_freaker'),
                                                 self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        assert os.strerror(p.returncode).lower() == 'no data available'
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_empty_multiple_files(self):
        cmd = "%s %s %s -d '|' -o %s -c 0" % (os.path.join(script_path, 'gristle_freaker'), self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        assert os.strerror(p.returncode).lower() == 'no data available'
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0
        p.stdin.close()


    def test_full_single_file(self):
        """ Tests use of columns all against a single file.
        """
        cmd = "%s %s -c '1,2' -d '|' -o %s " % (os.path.join(script_path, 'gristle_freaker'), self.easy_fqfn, self.out_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        assert p.returncode == 0
        #for record in records.split('\n'):
        #    print record
        out_rec_cnt = 0
        for rec in fileinput.input(self.out_fqfn):
            out_rec_cnt += 1
            fields     = rec[:-1].split('-')
            key_col_1  = fields[0].strip()
            key_col_2  = fields[1].strip()
            freq_cnt   = int(fields[2])

            assert key_col_1 == 'A'
            assert key_col_2 == 'B'
            assert freq_cnt  == 100

        fileinput.close()
        assert out_rec_cnt == 1
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
        assert p.returncode == 0
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
        assert p.returncode == 0
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 100
        p.stdin.close()


    def test_file_with_columntype_all(self):
        cmd = "%s %s --columntype all -d '|' -o %s " % (os.path.join(script_path, 'gristle_freaker'),
                                               self.easy_fqfn,
                                               self.out_fqfn)
        #print cmd
        #print 'easy_fqfn: %s' % self.easy_fqfn
        #os.system('cat %s' % self.easy_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        for record in records.split('\n'):
            print record

        assert p.returncode == 0
        for rec in fileinput.input(self.out_fqfn):
            fields = rec[:-1].split('-')
            assert len(fields)    == 5

            # 4-part key because 'all':
            row_id = fields[0].strip()
            key_a  = fields[1].strip()
            key_b  = fields[2].strip()
            key_c  = fields[3].strip()

            # actual count of above occurances:
            cnt    = int(fields[4])

            assert 0 <= int(row_id) < 100
            assert key_a == 'A'
            assert key_b == 'B'
            assert key_c == 'C'
            assert int(cnt) == 1

        fileinput.close()
        p.stdin.close()


    def test_file_with_columntype_each(self):
        cmd = "%s %s --columntype each -d '|' -o %s " % (os.path.join(script_path, 'gristle_freaker'),
                                               self.easy_fqfn,
                                               self.out_fqfn)
        #print cmd
        #print 'easy_fqfn: %s' % self.easy_fqfn
        #os.system('cat %s' % self.easy_fqfn)
        p =  subprocess.Popen(cmd,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              close_fds=True,
                              shell=True)
        records =  p.communicate()[0]
        #for record in records.split('\n'):
        #    print record

        assert p.returncode == 0
        for rec in fileinput.input(self.out_fqfn):
            fields = rec[:-1].split('-')
            col = fields[0].strip()
            val = fields[1].strip()
            cnt = int(fields[2])

            assert len(fields)    == 3

            if col == 'col:000':
                assert 0 <= int(val) < 100
                assert int(cnt) == 1
            elif col == 'col:001':
                assert val == 'A'
                assert int(cnt) == 100
            elif col == 'col:002':
                assert val == 'B'
                assert int(cnt) == 100
            elif col == 'col:003':
                assert val == 'C'
                assert int(cnt) == 100

        fileinput.close()
        p.stdin.close()

