#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
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
