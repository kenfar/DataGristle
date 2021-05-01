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
import tempfile

import envoy

import datagristle.common  as comm

# lets get pathing set for running code out of project structure & testing it via tox
script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm = os.path.join(script_path, 'gristle_slicer')




class Test7x7File(object):

    def setup_method(self, method):

        self.std_7x7_fqfn = self._generate_7x7_file()
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='TestSlice7x7Out_')

    def teardown_method(self, method):
        os.remove(self.std_7x7_fqfn)
        os.remove(self.out_fqfn)

    def _generate_7x7_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicer7x7In_')
        fp = os.fdopen(fd, "wt")
        fp.write('0-0,0-1,0-2,0-3,0-4,0-5,0-6\n')
        fp.write('1-0,1-1,1-2,1-3,1-4,1-5,1-6\n')
        fp.write('2-0,2-1,2-2,2-3,2-4,2-5,2-6\n')
        fp.write('3-0,3-1,3-2,3-3,3-4,3-5,3-6\n')
        fp.write('4-0,4-1,4-2,4-3,4-4,4-5,4-6\n')
        fp.write('5-0,5-1,5-2,5-3,5-4,5-5,5-6\n')
        fp.write('6-0,6-1,6-2,6-3,6-4,6-5,6-6\n')
        fp.close()
        return fqfn


    def runner(self, incl_rec_spec=None, excl_rec_spec=None,
               incl_col_spec=None, excl_col_spec=None,
               options=None):

        in_fqfn = self.std_7x7_fqfn
        out_fqfn = self.out_fqfn
        irs = comm.coalesce(' ', f"{incl_rec_spec}")
        ers = comm.coalesce(' ', f"{excl_rec_spec}")
        ics = comm.coalesce(' ', f"{incl_col_spec}")
        ecs = comm.coalesce(' ', f"{excl_col_spec}")
        opt = comm.coalesce(' ', f"{options}")
        pgm = fq_pgm  # get it local for string formatting

        cmd = f'''{pgm}  -i {in_fqfn}
                         -o {out_fqfn}
                         {irs}
                         {ers}
                         {ics}
                         {ecs}
                         {opt}
               '''
        r = envoy.run(cmd)
        if r.status_code:
            print('Status Code:  %d' % r.status_code)
            print(r.std_out)
            print(r.std_err)
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec[:-1])
        fileinput.close()

        return p_recs


    def test_select_first_row(self):

        valid = []
        valid.append('0-0,0-1,0-2,0-3,0-4,0-5,0-6')

        actual = self.runner('-r 0', None, None, None,
                             options='''--delimiter=',' --quoting=quote_none --has-no-header''')
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
                             options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_first_cell(self):

        valid = []
        valid.append('0-0')

        actual = self.runner('-r 0', None, '-c 0', None,
                             options='''--delimiter=',' --quoting=quote_none ''')
        assert valid == actual


    def test_select_first_4rows_except_2nd(self):

        valid = []
        valid.append('0-0,0-1,0-2,0-3,0-4,0-5,0-6')
        valid.append('2-0,2-1,2-2,2-3,2-4,2-5,2-6')
        valid.append('3-0,3-1,3-2,3-3,3-4,3-5,3-6')

        actual = self.runner('-r :4', '-R 1', None, None,
                             options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_four_corner_cells(self):

        valid = []
        valid.append('0-0,0-6')
        valid.append('6-0,6-6')

        actual = self.runner('-r 0,-1', None, '-c 0,-1', None,
                             options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual

        actual = self.runner('-r 0,-1', None, None, '-C 1:-1',
                             options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_asking_for_too_much(self):

        valid = []
        valid.append('0-0,0-1,0-2,0-3,0-4,0-5,0-6')

        actual = self.runner('-r 0', None, '-c 0:100', None,
                             options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual



class TestEmptyFile(object):

    def setup_method(self, method):
        self.empty_fqfn = self._generate_empty_file()
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='TestSliceEmptyOut_')

    def teardown_method(self, method):
        os.remove(self.empty_fqfn)
        os.remove(self.out_fqfn)

    def _generate_empty_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicerEmptyIn_')
        fp = os.fdopen(fd, "wt")
        fp.close()
        return fqfn

    def test_empty_file(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f"""{fq_pgm} -i {self.empty_fqfn} -o {self.out_fqfn} -r 15:20 """
        r = envoy.run(cmd)
        print(r.std_out)
        print(r.std_err)
        assert r.status_code == errno.ENODATA
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

    def test_empty_stdin(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f"""cat {self.empty_fqfn} | {fq_pgm}
                                          -d ',' -q quote_none --has-no-header
                                          -o {self.out_fqfn} -r 15:20"""
        r = envoy.run(cmd)
        print(r.std_out)
        print(r.std_err)
        assert r.status_code == errno.ENODATA
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

    def test_negative_offset_with_empty_stdin(self):
        """ Should return error since stdin can't have negative offsets
        """
        cmd = "cat %s , %s -d ',' -o %s -r -1:" % (self.empty_fqfn, fq_pgm, self.out_fqfn)
        r = envoy.run(cmd)
        assert r.status_code == 1
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


