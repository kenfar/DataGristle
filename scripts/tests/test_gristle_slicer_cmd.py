#!/usr/bin/env python
""" To do:
      1.  test with multiple input files

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
import pytest

#--- gristle modules -------------------
import test_tools

# lets get pathing set for running code out of project structure & testing it via tox
script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm      = os.path.join(script_path, 'gristle_slicer')
sys.path.insert(0, test_tools.get_app_root())

import gristle.common  as comm



class Test7x7File(object):

    def setup_method(self, method):

        self.std_7x7_fqfn       = self._generate_7x7_file()
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestSlice7x7Out_')

    def teardown_method(self, method):
        os.remove(self.std_7x7_fqfn)
        os.remove(self.out_fqfn)

    def _generate_7x7_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicer7x7In_')

        fp = os.fdopen(fd,"w")
        fp.write('0-0|0-1|0-2|0-3|0-4|0-5|0-6\n')
        fp.write('1-0|1-1|1-2|1-3|1-4|1-5|1-6\n')
        fp.write('2-0|2-1|2-2|2-3|2-4|2-5|2-6\n')
        fp.write('3-0|3-1|3-2|3-3|3-4|3-5|3-6\n')
        fp.write('4-0|4-1|4-2|4-3|4-4|4-5|4-6\n')
        fp.write('5-0|5-1|5-2|5-3|5-4|5-5|5-6\n')
        fp.write('6-0|6-1|6-2|6-3|6-4|6-5|6-6\n')

        fp.close()
        return fqfn


    def runner(self, incl_rec_spec=None, excl_rec_spec=None,
                     incl_col_spec=None, excl_col_spec=None,
                     options=None):

        in_fqfn  = self.std_7x7_fqfn
        out_fqfn = self.out_fqfn
        irs = comm.coalesce(' ', "%(incl_rec_spec)s" % locals())
        ers = comm.coalesce(' ', "%(excl_rec_spec)s" % locals())
        ics = comm.coalesce(' ', "%(incl_col_spec)s" % locals())
        ecs = comm.coalesce(' ', "%(excl_col_spec)s" % locals())
        opt = comm.coalesce(' ', "%(options)s"       % locals())
        pgm = fq_pgm  # get it local for string formatting

        cmd = '''%(pgm)s %(in_fqfn)s     \
                         -o %(out_fqfn)s \
                         %(irs)s         \
                         %(ers)s         \
                         %(ics)s         \
                         %(ecs)s         \
                         %(opt)s         \
              ''' % locals()
        r = envoy.run(cmd)
        if r.status_code:
            print 'Status Code:  %d' % r.status_code
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec[:-1])
        fileinput.close()

        return p_recs

    def test_select_all(self):

        valid = []
        valid.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')
        valid.append('1-0|1-1|1-2|1-3|1-4|1-5|1-6')
        valid.append('2-0|2-1|2-2|2-3|2-4|2-5|2-6')
        valid.append('3-0|3-1|3-2|3-3|3-4|3-5|3-6')
        valid.append('4-0|4-1|4-2|4-3|4-4|4-5|4-6')
        valid.append('5-0|5-1|5-2|5-3|5-4|5-5|5-6')
        valid.append('6-0|6-1|6-2|6-3|6-4|6-5|6-6')

        actual = self.runner(None, None, None, None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_first_row(self):

        valid = []
        valid.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')

        actual = self.runner('-r 0', None, None, None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_first_col(self):

        valid = []
        valid.append('0-0')
        valid.append('1-0')
        valid.append('2-0')
        valid.append('3-0')
        valid.append('4-0')
        valid.append('5-0')
        valid.append('6-0')

        actual = self.runner(None, None, '-c 0', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_first_cell(self):

        valid = []
        valid.append('0-0')

        actual = self.runner('-r 0', None, '-c 0', None,
                             options='''--delimiter='|' --quoting=quote_none ''')
        assert valid == actual

    def test_select_first_4rows(self):

        valid = []
        valid.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')
        valid.append('1-0|1-1|1-2|1-3|1-4|1-5|1-6')
        valid.append('2-0|2-1|2-2|2-3|2-4|2-5|2-6')
        valid.append('3-0|3-1|3-2|3-3|3-4|3-5|3-6')

        actual = self.runner('-r :4', None, None, None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_first_4rows_except_2nd(self):

        valid = []
        valid.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')
        valid.append('2-0|2-1|2-2|2-3|2-4|2-5|2-6')
        valid.append('3-0|3-1|3-2|3-3|3-4|3-5|3-6')

        actual = self.runner('-r :4', '-R 1', None, None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_four_corner_cells(self):

        valid = []
        valid.append('0-0|0-6')
        valid.append('6-0|6-6')

        actual = self.runner('-r 0,-1', None, '-c 0,-1', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

        actual = self.runner('-r 0,-1', None, None, '-C 1:-1',
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_the_middle(self):

        valid = []
        valid.append('1-1|1-2|1-3|1-4|1-5')
        valid.append('2-1|2-2|2-3|2-4|2-5')
        valid.append('3-1|3-2|3-3|3-4|3-5')
        valid.append('4-1|4-2|4-3|4-4|4-5')
        valid.append('5-1|5-2|5-3|5-4|5-5')

        actual = self.runner('-r 1:-1', None, '-c 1:-1', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

        actual = self.runner(None, '-R 0,-1', None, '-C 0,-1',
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_rows3and5_and_cols_2456(self):

        valid = []
        valid.append('2-2|2-4|2-5|2-6')
        valid.append('4-2|4-4|4-5|4-6')

        actual = self.runner('-r 2:5', '-R 3', '-c 2,4:7', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

        actual = self.runner('-r 2,4', None, '-c 2,4,5,6', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual

    def test_select_asking_for_too_much(self):

        valid = []
        valid.append('0-0|0-1|0-2|0-3|0-4|0-5|0-6')

        actual = self.runner('-r 0', None, '-c 0:100', None,
                             options='''--delimiter='|' --quoting=quote_none''')
        assert valid == actual



class TestEmptyFile(object):

    def setup_method(self, method):
        self.empty_fqfn         = self._generate_empty_file()
        (dummy, self.out_fqfn)  = tempfile.mkstemp(prefix='TestSliceEmptyOut_')

    def teardown_method(self, method):
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)

    def _generate_empty_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicerEmptyIn_')
        fp = os.fdopen(fd,"w")
        fp.close()
        return fqfn

    def test_empty_file(self):
        """ Should show proper handling of an empty file.
        """
        cmd = '%s %s -o %s -r 15:20' % (fq_pgm, self.empty_fqfn, self.out_fqfn)
        r = envoy.run(cmd)
        assert r.status_code == 0
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0

    def test_empty_stdin(self):
        """ Should show proper handling of an empty file.
        """
        cmd = "cat %s | %s -d '|' -o %s -r 15:20" % (self.empty_fqfn, fq_pgm, self.out_fqfn)
        r = envoy.run(cmd)
        assert r.status_code == 0
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0

    def test_negative_offset_with_empty_stdin(self):
        """ Should return error since stdin can't have negative offsets
        """
        cmd = "cat %s | %s -d '|' -o %s -r -1:" % (self.empty_fqfn, fq_pgm, self.out_fqfn)
        r = envoy.run(cmd)
        assert r.status_code == 1
        out_recs  = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0



class TestCSVDialects(object):

    def setup_method(self, method):

        self.nq_fqfn       = self._generate_nonquoted_file()
        self.q_fqfn        = self._generate_quoted_file()
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='TestSlice4x4Out_')

    def teardown_method(self, method):
        os.remove(self.nq_fqfn)
        os.remove(self.q_fqfn)
        os.remove(self.out_fqfn)

    def _generate_nonquoted_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicerNQIn_')
        fp = os.fdopen(fd,"w")
        fp.write('0a0|0e1|0i2|0m3\n')
        fp.write('1b0|1f1|1j2|1n3\n')
        fp.write('2c0|2g1|2k2|2o3\n')
        fp.write('3d0|3h1|3l2|3p3\n')
        fp.close()
        return fqfn

    def _generate_quoted_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicerQIn_')
        fp = os.fdopen(fd,"w")
        fp.write('"0a0"|"0e1"|"0i2"|"0m3"\n')
        fp.write('"1b0"|"1f1"|"1j2"|"1n3"\n')
        fp.write('"2c0"|"2g1"|"2k2"|"2o3"\n')
        fp.write('"3d0"|"3h1"|"3l2"|"3p3"\n')
        fp.close()
        return fqfn

    def runner(self, incl_rec_spec=None, excl_rec_spec=None,
                     incl_col_spec=None, excl_col_spec=None,
                     quoted_file=False,
                     options=None,
                     runtype='arg'):

        assert runtype in ['arg','stdin']

        if quoted_file:
            in_fqfn = self.q_fqfn
        else:
            in_fqfn = self.nq_fqfn

        irs      = comm.coalesce(' ', "'%(incl_rec_spec)s'" % locals())
        ers      = comm.coalesce(' ', "'%(excl_rec_spec)s'" % locals())
        ics      = comm.coalesce(' ', "'%(incl_col_spec)s'" % locals())
        ecs      = comm.coalesce(' ', "'%(excl_col_spec)s'" % locals())
        opt      = comm.coalesce(' ', "%(options)s"         % locals())
        pgm      = fq_pgm  # get it local for string formatting
        out_fqfn = self.out_fqfn


        def run_cmd(cmd):
            r    = envoy.run(cmd)
            recs = []
            for rec in fileinput.input(self.out_fqfn):
                recs.append(rec[:-1])
            fileinput.close()
            return r.status_code, recs


        if runtype == 'arg':
            arg_cmd = '''%(pgm)s    %(in_fqfn)s             \
                                    -o %(out_fqfn)s         \
                                    %(irs)s                 \
                                    %(ers)s                 \
                                    %(ics)s                 \
                                    %(ecs)s                 \
                                    %(opt)s                 \
                      ''' % locals()
            rc, recs = run_cmd(arg_cmd)
        else:
            stdin_cmd = '''cat %(in_fqfn)s | %(pgm)s        \
                                    -o %(out_fqfn)s         \
                                    %(irs)s                 \
                                    %(ers)s                 \
                                    %(ics)s                 \
                                    %(ecs)s                 \
                                    %(opt)s                 \
                        ''' % locals()
            rc, recs = run_cmd(stdin_cmd)

        return rc, recs


    def test_select_first_cell(self):

        #--------- non-quoted input, non-quoted processing: --------------
        valid = ['0a0']
        rc, actual = self.runner('-r 0', None, '-c 0', None,
                                 quoted_file=False,
                                 runtype='arg')
        assert valid == actual
        assert rc == 0

        rc, actual = self.runner('-r 0', None, '-c 0', None,
                                 quoted_file=False,
                                 runtype='stdin')
        # must fail because it's missing delimiter info for stdin
        assert rc == 2


        #-------- non-quoted input, non-quoted processing with delimiter and quoting override:
        valid = []
        valid.append('0a0')
        rc, actual = self.runner('-r 0', None, '-c 0', None, quoted_file=False,
                                 options='''--delimiter='|' --quoting=quote_none ''' ,
                                 runtype='arg')
        assert valid == actual
        assert rc == 0

        rc, actual = self.runner('-r 0', None, '-c 0', None, quoted_file=False,
                                 options='''--delimiter='|' --quoting=quote_none ''' ,
                                 runtype='stdin')
        assert valid == actual
        assert rc == 0

        #--------------- quoted input, quoted processing with delimiter and quoting override:
        valid = []
        valid.append('"0a0"')
        rc, actual = self.runner('-r 0', None, '-c 0', None, quoted_file=True,
                                 options='''--delimiter='|' --quoting=quote_all''',
                                 runtype='arg')
        assert valid == actual
        assert rc == 0

        rc, actual = self.runner('-r 0', None, '-c 0', None, quoted_file=True,
                                 options='''--delimiter='|' --quoting=quote_all''',
                                 runtype='stdin')
        assert valid == actual
        assert rc == 0


        #---------------- quoted input, quoted processing:
        valid = []
        valid.append('"0a0"')
        rc, actual = self.runner('-r 0', None, '-c 0', None, quoted_file=True,
                                 runtype='arg')
        assert valid == actual
        assert rc == 0



