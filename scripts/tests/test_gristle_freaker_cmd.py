#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

import tempfile
import fileinput
import subprocess
from pprint import pprint as pp
import os
from os.path import dirname, join as pjoin

import envoy

import datagristle.test_tools as test_tools

script_dir = dirname(dirname(os.path.realpath((__file__))))
data_dir = pjoin(dirname(script_dir), 'data')




class TestCSVDialect(object):

    def setup_method(self, method):
        (_, self.out_fqfn) = tempfile.mkstemp(prefix='TestFreakerOut_')
        self.out_recs = []

    def teardown_method(self, method):
        os.remove(self.out_fqfn)


    def test_noheader_file_with_no_header_args(self):
        in_fqfn = os.path.join(data_dir, '3x3.csv')
        cmd = "%s -i %s -d ',' -o %s -c 0" \
              % (os.path.join(script_dir, 'gristle_freaker'), in_fqfn, self.out_fqfn)
        runner = self.executor(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert len(self.out_recs) == 3

    def test_noheader_file_with_hasnoheader_arg(self):
        in_fqfn = os.path.join(data_dir, '3x3.csv')
        cmd = "%s -i %s -d ',' -o %s -c 0 --has-no-header" \
              % (os.path.join(script_dir, 'gristle_freaker'), in_fqfn, self.out_fqfn)
        self.executor(cmd)
        assert len(self.out_recs) == 3

    def test_header_file_with_no_header_args(self):
        in_fqfn = os.path.join(data_dir, '3x3_header.csv')
        cmd = "%s -i %s -d ',' -o %s -c 0 --verbosity debug " \
            % (os.path.join(script_dir, 'gristle_freaker'), in_fqfn, self.out_fqfn)
        self.executor(cmd)
        pp(self.out_recs)
        assert len(self.out_recs) == 3

    def test_header_file_with_hasheader_arg(self):
        in_fqfn = os.path.join(data_dir, '3x3_header.csv')
        cmd = "%s -i %s -d ',' -o %s -c 0 --has-header" \
              % (os.path.join(script_dir, 'gristle_freaker'), in_fqfn, self.out_fqfn)
        self.executor(cmd)
        assert len(self.out_recs) == 3

    def executor(self, cmd):
        runner = envoy.run(cmd)
        for rec in fileinput.input(self.out_fqfn):
            self.out_recs.append(rec[:-1])
        print(runner.std_out)
        print(runner.std_err)
        print(self.out_recs)
        assert runner.status_code == 0
        return runner



class TestCommandLine(object):

    def setup_method(self, method):

        self.easy_fqfn = generate_test_file(delim='|',
                                            record_cnt=100,
                                            name='easy')
        self.empty_fqfn = generate_test_file(delim='|',
                                             record_cnt=0,
                                             name='empty')
        (_, self.out_fqfn) = tempfile.mkstemp(prefix='TestFreakerOut_')

    def teardown_method(self, method):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestFreaker'))

    def test_empty_file(self):
        cmd = '%s -i %s -o %s -c 0' % (os.path.join(script_dir, 'gristle_freaker'),
                                    self.empty_fqfn, self.out_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        _ = runner.communicate()[0]
        print('returncode:')
        print(runner.returncode)
        # We've got different messages here that mean essentially the same
        # thing, which you get depends on platform.
        print(os.strerror(runner.returncode).lower())
        assert os.strerror(runner.returncode).lower() in ['no data available',
                                                          'no message available on stream']
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs
        runner.stdin.close()


    def test_empty_stdin_file(self):

        cmd = f"""cat {self.empty_fqfn} | {os.path.join(script_dir, 'gristle_freaker')}
                                           -d ',' -q quote_none --has-no-header
                                           -o {self.out_fqfn} -c 2"""
        r = envoy.run(cmd)
        print(r.std_out)
        print(r.std_err)
        assert r.status_code == 61
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


    def test_empty_multiple_files(self):
        cmd = "%s -i %s %s -d '|' -o %s -c 0" \
              % (os.path.join(script_dir, 'gristle_freaker'), self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        _ = runner.communicate()[0]
        # We've got different messages here that mean essentially the same
        # thing, which you get depends on platform.
        assert os.strerror(runner.returncode).lower() in ['no data available',
                                                          'no message available on stream']
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs
        runner.stdin.close()


    def test_full_single_file(self):
        """ Tests use of columns all against a single file.
        """
        cmd = "%s -i %s -c 1 2 -d '|' -o %s " % (os.path.join(script_dir, 'gristle_freaker'), self.easy_fqfn, self.out_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        _ = runner.communicate()[0]
        assert runner.returncode == 0
        out_rec_cnt = 0
        for rec in fileinput.input(self.out_fqfn):
            out_rec_cnt += 1
            fields = rec[:-1].split('-')
            key_col_1 = fields[0].strip()
            key_col_2 = fields[1].strip()
            freq_cnt = int(fields[2])

            assert key_col_1 == 'A'
            assert key_col_2 == 'B'
            assert freq_cnt == 100

        fileinput.close()
        assert out_rec_cnt == 1
        runner.stdin.close()


    def test_full_multiple_files(self):
        cmd = "%s -i %s %s -d '|' -o %s -c 0" % (os.path.join(script_dir, 'gristle_freaker'),
                                              self.easy_fqfn, self.easy_fqfn, self.out_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        output = cleaner(runner.communicate()[0])
        pp(output)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        runner.stdin.close()
        pp(out_recs)
        assert runner.returncode == 0
        assert len(out_recs) == 100


    def test_empty_and_full_multiple_files(self):
        cmd = "%s -i %s %s -d '|' -o %s -c 0" % (os.path.join(script_dir, 'gristle_freaker'),
                                              self.empty_fqfn, self.easy_fqfn, self.out_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        records = cleaner(runner.communicate()[0])
        for record in records.split('\n'):
            print(record)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 100
        runner.stdin.close()
        assert runner.returncode == 0


    def test_file_with_col_type_all(self):
        cmd = "%s -i %s --col-type all -d '|' -o %s " \
           % (os.path.join(script_dir, 'gristle_freaker'), self.easy_fqfn, self.out_fqfn)
        #print cmd
        #print 'easy_fqfn: %s' % self.easy_fqfn
        #os.system('cat %s' % self.easy_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        records = cleaner(runner.communicate()[0])
        for record in records.split('\n'):
            print(record)

        assert runner.returncode == 0
        for rec in fileinput.input(self.out_fqfn):
            fields = rec[:-1].split('-')
            assert len(fields) == 5

            # 4-part key because 'all':
            row_id = fields[0].strip()
            key_a = fields[1].strip()
            key_b = fields[2].strip()
            key_c = fields[3].strip()

            # actual count of above occurances:
            cnt = int(fields[4])

            assert 0 <= int(row_id) < 100
            assert key_a == 'A'
            assert key_b == 'B'
            assert key_c == 'C'
            assert int(cnt) == 1

        fileinput.close()
        runner.stdin.close()


    def test_file_with_col_type_each(self):
        cmd = "%s -i %s --col-type each -d '|' -o %s " \
               % (os.path.join(script_dir, 'gristle_freaker'), self.easy_fqfn, self.out_fqfn)
        #print cmd
        #print 'easy_fqfn: %s' % self.easy_fqfn
        #os.system('cat %s' % self.easy_fqfn)
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        _ = runner.communicate()[0]
        assert runner.returncode == 0
        for rec in fileinput.input(self.out_fqfn):
            fields = rec[:-1].split('-')
            col = fields[0].strip()
            val = fields[1].strip()
            cnt = int(fields[2])

            assert len(fields) == 3

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
        runner.stdin.close()



def cleaner(val):
    if val is None:
        return ''
    elif type(val) is bytes:
        return val.decode()
    else:
        return val



def generate_test_file(delim, record_cnt, name='generic'):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestFreakerIn_%s_' % name)
    fp = os.fdopen(fd, "w")

    for i in range(record_cnt):
        fields = []
        fields.append(str(i))
        fields.append('A')
        fields.append('B')
        fields.append('C')
        fp.write(delim.join(fields)+'\n')

    fp.close()
    return fqfn
