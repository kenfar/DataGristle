#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2017 Ken Farmer
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
import os
from os.path import dirname, join as pjoin

import envoy
import datagristle.test_tools as test_tools

script_path = dirname(dirname(os.path.realpath((__file__))))
fq_pgm = pjoin(script_path, 'gristle_viewer')



def generate_test_file(delim, record_cnt):
    (fd, fqfn) = tempfile.mkstemp(prefix='ViewerTestIn_')
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



class TestCommandLine(object):

    def setup_method(self, method):
        self.in_fqfn = generate_test_file(delim=',', record_cnt=100)
        self.empty_fqfn = generate_test_file(delim=',', record_cnt=0)
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='ViewerTestOut_')

    def teardown_method(self, method):
        os.remove(self.in_fqfn)
        os.remove(self.out_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'ViewerTest'))

    def test_easy_file(self):
        cmd = '%s -i %s -r 9 -o %s' % (fq_pgm, self.in_fqfn, self.out_fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0

        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec)
        fileinput.close()

        assert len(p_recs) == 4

        assert p_recs[0].strip().startswith('field_0')
        assert p_recs[0].strip().endswith('9')

        assert p_recs[1].strip().startswith('field_1')
        assert p_recs[1].strip().endswith('A')

        assert p_recs[2].strip().startswith('field_2')
        assert p_recs[2].strip().endswith('B')

        assert p_recs[3].strip().startswith('field_3')
        assert p_recs[3].strip().endswith('C')


    def test_bad_recnum(self):
        """ Shows that the program when given a recnum that doesn't exist will
            write no rows to the output file and print only a comment to stdout

            To do:
                - check for a negative number
                - check for return code
        """

        p_outrecs = []
        cmd = '%s -i %s -r 999 -o %s' % (fq_pgm, self.in_fqfn, self.out_fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0
        for rec in fileinput.input(self.out_fqfn):
            p_outrecs.append(rec)
        fileinput.close()

        assert 'No record found' in runner.std_out
        assert not p_outrecs


    def test_empty_file(self):
        cmd = "%s -i %s -o %s -r 999 " % (fq_pgm, self.empty_fqfn, self.out_fqfn)
        _ = envoy.run(cmd)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


    def test_full_multiple_files(self):
        cmd = "%s -i %s %s -o %s -r 9 -d','" % (fq_pgm, self.in_fqfn, self.in_fqfn, self.out_fqfn)
        _ = envoy.run(cmd)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()

        assert len(out_recs) == 4
        assert out_recs[0].strip().startswith('field_0')
        assert out_recs[0].strip().endswith('9')


    def test_full_multiple_empty_files(self):
        cmd = "%s -i %s %s -o %s -r 9 -d',' " % (fq_pgm, self.empty_fqfn, self.empty_fqfn, self.out_fqfn)
        _ = envoy.run(cmd)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


    def test_full_multiple_empty_and_full_files(self):
        # NOTE: this test only passes if non-empty file is provided first!
        cmd = "%s -i %s %s -o %s -r 9 -d','" % (fq_pgm, self.in_fqfn, self.empty_fqfn, self.out_fqfn)
        _ = envoy.run(cmd)
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()

        assert len(out_recs) == 4
        assert out_recs[0].strip().startswith('field_0')
        assert out_recs[0].strip().endswith('9')
