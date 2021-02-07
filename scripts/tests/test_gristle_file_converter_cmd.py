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
import subprocess
import os
from os.path import dirname
from pprint import pprint as pp

import envoy
import pytest

SCRIPT_PATH = dirname(dirname(os.path.realpath((__file__))))
PGM = os.path.join(SCRIPT_PATH, 'gristle_file_converter')



class TestCommandLine(object):

    def setup_method(self, method):
        self.easy_fqfn = generate_test_file(delim='$', record_cnt=100)
        self.empty_fqfn = generate_test_file(delim='$', record_cnt=0)

    def teardown_method(self, method):
        os.remove(self.easy_fqfn)
        os.remove(self.empty_fqfn)

    def test_input_and_output_del(self):
        cmd = f"{PGM} -i {self.easy_fqfn} -d '$' -D ',' "
        runner = subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)
        r_output = cleaner(runner.communicate()[0])
        r_recs = r_output[:-1].split('\n')

        for rec in r_recs:
            assert rec.count(',') == 3
        assert len(r_recs) == 100


    def test_output_del_only(self):
        cmd = f"{PGM} -i {self.easy_fqfn} -D ',' "
        runner = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  close_fds=True,
                                  shell=True)

        r_output = cleaner(runner.communicate()[0])
        r_recs = r_output[:-1].split('\n')
        for rec in r_recs:
            assert rec.count(',') == 3
        assert len(r_recs) == 100


    def test_empty_file(self):
        cmd = f"{PGM} -i {self.easy_fqfn} -D ',' "
        runner = subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  shell=True)
        r_output = cleaner(runner.communicate()[0])
        out_recs = r_output[:-1].split('\n')
        if not out_recs:
            pytest.fail('produced output when input was empty')



def cleaner(val):
    if val is None:
        return ''
    elif type(val) is bytes:
        return val.decode()
    else:
        return val



def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp()
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
