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

import errno
import fileinput
import os
import shutil
import tempfile
from os.path import join as pjoin, dirname
from pprint import pprint as pp

import envoy
import ruamel.yaml as yaml

import datagristle.test_tools as test_tools

script_dir = dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm = pjoin(script_dir, 'gristle_validator')




def _generate_foobar_file(recs, dir_name, quoting='quote_none'):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorIn_', dir=dir_name)
    fp = os.fdopen(fd,"w")
    for rec in range(recs):
        if quoting == 'quote_all':
            rec = '"foo","bar","batz","1.9","2","%d"' % rec
        elif quoting == 'quote_nonnumeric':
            rec = '"foo","bar","batz",1.9,2,%d' % rec
        elif quoting == 'quote_none':
            rec = 'foo,bar,batz,1.9,2,%d' % rec
        else:
            raise ValueError("Invalid quoting: %s" % quoting)
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn



class TestFieldCount(object):
    """ Tests gristle_validator functionality involved in verifying
        that all records within a file have the correct number of fields.
    """


    def setup_method(self, method):

        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.pgm = fq_pgm
        self.std_7x7_fqfn, self.data_7x7 = test_tools.generate_7x7_test_file('TestGristleValidator7x7In_',
                                                                             delimiter=',', dirname=self.tmp_dir)
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_', dir=self.tmp_dir)

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def get_outputs(self, response):
        print(response.status_code)
        print(response.std_out)
        print(response.std_err)

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out = response.std_out
        self.std_err = response.std_err
        self.good_output = good_recs
        self.err_output = err_recs


    def test_stats_option(self):
        """ The stats option will create a report to stdout
            The stats should look like this:
                input_cnt        | 7
                invalid_cnt      | 7
                valid_cnt        | 0
        """
        self.cmd = """%(pgm)s                      \
                         --infiles %(in_fqfn)s     \
                         -d ','                    \
                         --field-cnt 70             \
                         --quoting 'quote_none'    \
                         --outfile %(outfile)s     \
                         --errfile  %(errfile)s    \
                         --verbosity high          \
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == errno.EBADMSG
        assert self.err_output
        assert not self.good_output
        assert self.std_out
        assert self.std_out
        # std_err should be 0, but coverage.py might write 46 bytes to it:
        assert not self.std_err or (len(self.std_err) < 50 and 'Coverage.py' in self.std_err)

        std_out_recs = self.std_out.split('\n')
        input_cnt_found = False
        invalid_cnt_found = False
        valid_cnt_found = False

        for rec in std_out_recs:
            if not rec:
                continue
            fields = rec.split('|')
            assert len(fields) == 2

            if fields[0].strip() == 'input_cnt':
                assert fields[1].strip() == '7'
                input_cnt_found = True
            elif fields[0].strip() == 'invalid_cnt':
                assert fields[1].strip() == '7'
                invalid_cnt_found = True
            elif fields[0].strip() == 'valid_cnt':
                assert fields[1].strip() == '0'
                valid_cnt_found = True

        assert input_cnt_found
        assert invalid_cnt_found
        assert valid_cnt_found


    def test_random_out_1(self):
        in_fqfn = _generate_foobar_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 1.0
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert len(self.good_output) == 10000


    def test_random_out_0(self):
        in_fqfn = _generate_foobar_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 0
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert not self.good_output


    def test_random_out_01(self):

        in_fqfn = _generate_foobar_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 0.1
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert (0.2 * 100000) > len(self.good_output) > (0.05 * 10000)



class TestEmptyFile(object):

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.empty_fqfn = self._generate_empty_file()
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutErr_', dir=self.tmp_dir)

    def _generate_empty_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyIn_', dir=self.tmp_dir)
        fp = os.fdopen(fd, "w")
        fp.close()
        return fqfn

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def test_empty_file(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f'''{fq_pgm} \
                  --infiles {self.empty_fqfn} \
                  --outfile {self.outgood_fqfn} \
                  --errfile {self.outerr_fqfn} \
                  -f 5
                  -d ','
                  -q quote_none
               '''
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == errno.ENODATA

        out_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

        out_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


    def test_empty_stdin(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f"""cat {self.empty_fqfn} | {fq_pgm} -d',' -f 5
                        --outfile {self.outgood_fqfn}
                        --errfile {self.outerr_fqfn}
                        -d ','
                        -q quote_none
                        --has-no-header
               """
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == errno.ENODATA

        out_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

        out_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs



def print_file(fn):
    pp('++++++++++++++++++++++++++++++++++++++++++++++++')
    for rec in fileinput.input(fn):
        print(rec)
    pp('++++++++++++++++++++++++++++++++++++++++++++++++')


