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
from pprint import pprint as pp
import subprocess
import tempfile
import time

import envoy
import pytest

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


    def runner(self,
               incl_rec_spec=None, excl_rec_spec=None,
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
                         --verbosity debug
               '''
        r = envoy.run(cmd)
        if r.status_code:
            print('Status Code:  %d' % r.status_code)
            print(r.std_out)
            print(r.std_err)
        print(r.std_out)
        print(r.std_err)
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec[:-1])
        fileinput.close()

        return r.status_code, p_recs


    def test_select_first_row(self):

        valid = []
        valid.append('0-0,0-1,0-2,0-3,0-4,0-5,0-6')

        rc, actual = self.runner('-r 0', None, None, None,
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

        rc, actual = self.runner(None, None, '-c 0', None,
                     options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_first_cell(self):

        valid = []
        valid.append('0-0')

        rc, actual = self.runner('-r 0', None, '-c 0', None,
                     options='''--delimiter=',' --quoting=quote_none ''')
        assert valid == actual


    def test_select_first_4rows_except_2nd(self):

        valid = []
        valid.append('0-0,0-1,0-2,0-3,0-4,0-5,0-6')
        valid.append('2-0,2-1,2-2,2-3,2-4,2-5,2-6')
        valid.append('3-0,3-1,3-2,3-3,3-4,3-5,3-6')

        rc, actual = self.runner('-r :4', '-R 1', None, None,
                     options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_four_corner_cells(self):

        valid = []
        valid.append('0-0,0-6')
        valid.append('6-0,6-6')

        rc, actual = self.runner('-r 0,-1', None, '-c 0,-1', None,
                     options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual

        rc, actual = self.runner('-r 0,-1', None, None, '-C 1:-1',
                     options='''--delimiter=',' --quoting=quote_none''')
        assert valid == actual


    def test_select_asking_for_too_much(self):

        rc, _ = self.runner('-r 0:5', None, '-c 0:999', None,
                options='''--delimiter=',' --quoting=quote_none --max-mem-recs=1''')
        assert rc == 0



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
        cmd = f"""cat %s | {fq_pgm}
                           -d ',' -q quote_none --has-no-header
                           -o {self.out_fqfn} -r ' -10: ' """
        r = envoy.run(cmd)
        print(r.std_out)
        print(r.std_err)
        assert r.status_code == errno.ENODATA
        #assert r.status_code == 1
        out_recs = []
        for rec in fileinput.input(self.out_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs



class TestStdin(object):

    def setup_method(self, method):
        self.std_7x7_fqfn = self._generate_7x7_file()
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='TestSlice7x7Out_')

    def teardown_method(self, method):
        os.remove(self.std_7x7_fqfn)
        os.remove(self.out_fqfn)

    def _generate_7x7_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicer7x7In_')
        fp = os.fdopen(fd, "w")
        fp.write('0-0,0-1,0-2,0-3,0-4,0-5,0-6\n')
        fp.write('1-0,1-1,1-2,1-3,1-4,1-5,1-6\n')
        fp.write('2-0,2-1,2-2,2-3,2-4,2-5,2-6\n')
        fp.write('3-0,3-1,3-2,3-3,3-4,3-5,3-6\n')
        fp.write('4-0,4-1,4-2,4-3,4-4,4-5,4-6\n')
        fp.write('5-0,5-1,5-2,5-3,5-4,5-5,5-6\n')
        fp.write('6-0,6-1,6-2,6-3,6-4,6-5,6-6\n')
        fp.close()
        return fqfn


    def test_negative_offset(self):
        """ Should treat out of range single offspec specs as false rather than error.

        Using subprocess rather than envoy after fighting with an envoy bug too long.
        """

        rc = 0
        ps = subprocess.Popen(('cat', self.std_7x7_fqfn), stdout=subprocess.PIPE)
        try:
            subprocess.check_output((fq_pgm, '-d,', '-qquote_none', '--has-no-header',
                                     '-o', self.out_fqfn, '-r-1'), stdin=ps.stdout)
        except subprocess.CalledProcessError as err:
            rc = err.returncode
        assert rc == 0

        actual = load_file(self.out_fqfn)

        valid = []
        valid.append('6-0,6-1,6-2,6-3,6-4,6-5,6-6\n')

        actual = load_file(self.out_fqfn)
        assert valid == actual


def load_file(fn: str) -> list[str]:
    out_recs = []
    for rec in fileinput.input(fn):
        out_recs.append(rec)
    fileinput.close()
    return out_recs





@pytest.mark.slow
class TestPerformance(object):

    def setup_method(self, method):
        self.input_count = 1_000_000
        self.in_fqfn = self._generate_file()
        (dummy, self.out_fqfn) = tempfile.mkstemp(prefix='TestSlice7x7Out_')


    def teardown_method(self, method):
        os.remove(self.in_fqfn)
        os.remove(self.out_fqfn)


    def _generate_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestSlicer7x7In_')
        fp = os.fdopen(fd, "wt")
        for count in range(self.input_count):
            row = f'{count}-0,{count}-1,{count}-2,{count}-3,{count}-4,{count}-5,{count}-6\n'
            fp.write(row)
        fp.close()
        return fqfn


    def runner(self,
               incl_rec_spec=None, excl_rec_spec=None,
               incl_col_spec=None, excl_col_spec=None,
               options=None):

        in_fqfn = self.in_fqfn
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
                         --verbosity debug
               '''
        r = envoy.run(cmd)
        if r.status_code:
            print('Status Code:  %d' % r.status_code)
            print(r.std_out)
            print(r.std_err)
        print(r.std_out)
        print(r.std_err)
        p_recs = []
        for rec in fileinput.input(self.out_fqfn):
            p_recs.append(rec[:-1])
        fileinput.close()

        return r.status_code, p_recs


    def test_select_all(self):

        start_time = time.time()
        rc, actual = self.runner(None, None,
                     options='''--delimiter=',' --quoting=quote_none''')
        duration = time.time() - start_time
        pp(duration)
        assert 12 > duration > 8
        assert rec_cnt(self.out_fqfn) == self.input_count


    def test_skip_every_other(self):

        start_time = time.time()
        rc, actual = self.runner(incl_rec_spec='-r=::2',
                     options='''--delimiter=',' --quoting=quote_none''')
        duration = time.time() - start_time
        pp(duration)
        assert 12 > duration > 8
        assert rec_cnt(self.out_fqfn) == self.input_count / 2


    def test_short_circuit(self):

        start_time = time.time()
        rc, actual = self.runner(incl_rec_spec='-r=:10',
                     options='''--delimiter=',' --quoting=quote_none''')
        duration = time.time() - start_time
        pp(duration)
        assert 1 > duration > 0.1
        assert rec_cnt(self.out_fqfn) == 10


    def test_select_one_col(self):

        start_time = time.time()
        rc, actual = self.runner(incl_col_spec='-c=3',
                     options='''--delimiter=',' --quoting=quote_none''')
        duration = time.time() - start_time
        pp(duration)
        assert 8 > duration > 3
        assert rec_cnt(self.out_fqfn) == self.input_count


    def test_reverse_file(self):

        start_time = time.time()
        rc, actual = self.runner(incl_rec_spec='-r=::-1',
                                 incl_col_spec='-c=3',
                     options='''--delimiter=',' --quoting=quote_none''')
        duration = time.time() - start_time
        pp(duration)
        assert 8 > duration > 4
        assert rec_cnt(self.out_fqfn) == self.input_count



def rec_cnt(fqfn):
    for rec in fileinput.input(fqfn):
        pass
    rec_cnt = fileinput.lineno()
    fileinput.close()
    pp('==============================================')
    pp(rec_cnt)
    pp('==============================================')
    return rec_cnt





