#!/usr/bin/env python

# standard modules:
import sys
import os
import copy
import time
import tempfile
import shutil
import gzip
import fileinput
import csv

from os.path import dirname, basename
from os.path import isfile, isdir, exists
from os.path import join as pjoin

# third-party modules:
import envoy
import yaml
import pytest
import sqlalchemy as sql
from pprint import pprint as pp
import cletus.cletus_log            as logger_mgr


# gristle modules:
sys.path.insert(0, dirname('../'))
sys.path.insert(0, dirname('../../'))
sys.path.append('../../../../')

import datagristle.file_delta           as mod
from datagristle.csvhelper import create_dialect

LOG_NAME    = 'main'


class TestAssignment(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.fqfn     = create_test_file(self.temp_dir)
        self.dialect  = create_dialect(delimiter=',', quoting=csv.QUOTE_NONE, hasheader=False)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_set_assignment_args(self):
        dass  = mod.DeltaAssignments()
        with pytest.raises(ValueError):
            dass.set_assignment(None, None, None, None)
        with pytest.raises(ValueError):
            dass.set_assignment('foo', None, None, None)
        with pytest.raises(ValueError):
            dass.set_assignment('insert', 'foo', 'bar', None)
        with pytest.raises(ValueError):
            dass.set_assignment('delete', 3, 'literal', None)
        assert dass.set_assignment('insert',  3, 'literal', 'foo') is None
        assert dass.set_assignment('delete',  3, 'literal', 'foo') is None
        assert dass.set_assignment('chgold',  3, 'literal', 'foo') is None
        assert dass.set_assignment('chgnew',  3, 'literal', 'foo') is None
        assert dass.set_assignment('chgnew',  3, 'copy', src_file='old', src_field=5)   is None
        assert dass.set_assignment('chgnew',  3, 'literal', 'foo') is None

    def test_set_assignments(self):
        dass = mod.DeltaAssignments()
        dass.set_assignment('insert', 3, 'literal', 'foo')
        assert dass.assignments['insert'][3] == {'src_type': 'literal',
                                                  'src_val': 'foo',
                                                  'src_file': None,
                                                  'src_field':None}
        dass.set_assignment('chgold', 2, 'copy', src_file='new', src_field=2)
        assert dass.assignments['chgold'][2] == {'src_type': 'copy',
                                                  'src_val':  None,
                                                  'src_file': 'new',
                                                  'src_field':2}

    def test_assign_literal_to_different_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 2, 'literal', 'foo')
        dass.assign('delete', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', 'b', 'c', 'd']
        
    def test_assign_literal_to_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 2, 'literal', 'foo')
        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', 'b', 'foo', 'd']
        
    def test_assign_copy_oldfield_to_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 2, 'copy', None, 'old', 1)
        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', 'b', 'o1', 'd']

    def test_assign_copy_newfield_to_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('chgold', 2, 'copy', None, 'new', 1)
        dass.assign('chgold', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', 'b', 'n1', 'd']

    def test_assign_copy_oldfield_empty(self):
        old_rec = []
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 2, 'copy', None, 'old', 1)
        with pytest.raises(SystemExit):
            dass.assign('insert', cur_rec, old_rec, new_rec)

    def test_assign_two_copies_same_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('chgold', 2, 'copy', None, 'new', 1)
        dass.set_assignment('chgold', 1, 'copy', None, 'new', 2)
        dass.assign('chgold', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', 'n2', 'n1', 'd']

    def test_assign_sequence(self):
        old_rec = ['0', 'o1', 'o2', 'o3']
        new_rec = ['0', 'n1', 'n2', 'n3']
        cur_rec = ['', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 0, 'sequence', None, 'old', 0)

        fqfn    = pjoin(self.temp_dir, 'old.csv')
        with open(fqfn, 'w') as f:
             f.write('3,o,oo,ooo\n')
             f.write('5,o,oo,ooo\n')

        dass.get_sequence_starts(self.dialect, fqfn)
        print('---- post sequence_starts seq dict: -----')
        print(dass.seq)
        print('---- post sequence_starts print-done: -----')

        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['6', 'b', 'c', 'd']

    def test_assign_two_sequences_to_4fields(self):
        """ This shows that a single sequence can be used on multiple files without
            creating duplicates.
            It also shows that multiple sequences can be made from multiple sources.
        """
        old_rec = ['0', 'o1', 'o2', 'o3']
        new_rec = ['0', 'n1', 'n2', 'n3']
        cur_rec = ['', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 0, 'sequence', None, 'old', 0)
        dass.set_assignment('insert', 2, 'sequence', None, 'old', 2)
        dass.set_assignment('chgnew', 0, 'sequence', None, 'old', 0)
        dass.set_assignment('chgnew', 2, 'sequence', None, 'old', 2)

        fqfn    = pjoin(self.temp_dir, 'old.csv')
        with open(fqfn, 'w') as f:
             f.write('3,o,2,ooo\n')
             f.write('5,o,4,ooo\n')
             f.write('5,o,6,ooo\n')

        dass.get_sequence_starts(self.dialect, fqfn)
        print('---- post sequence_starts seq dict: -----')
        print(dass.seq)
        print('---- post sequence_starts print-done: -----')

        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['6', 'b', '7', 'd']

        dass.assign('chgnew', cur_rec, old_rec, new_rec)
        assert cur_rec == ['7', 'b', '8', 'd']

    def test_assign_sequences_empty_old(self):
        old_rec = None
        new_rec = ['0', 'n1', 'n2', 'n3']
        cur_rec = ['', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_assignment('insert', 0, 'sequence', None, 'old', 0)

        fqfn    = pjoin(self.temp_dir, 'old.csv')
        with open(fqfn, 'w') as f:
             pass

        dass.get_sequence_starts(self.dialect, fqfn)
        print('---- post sequence_starts seq dict: -----')
        print(dass.seq)
        print('---- post sequence_starts print-done: -----')

        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['1', 'b', 'c', 'd']

    def test_assign_specialvalue_to_rec(self):
        old_rec = ['o0', 'o1', 'o2', 'o3']
        new_rec = ['n0', 'n1', 'n2', 'n3']
        cur_rec = ['a', 'b', 'c', 'd']
        dass    = mod.DeltaAssignments()
        dass.set_special_values('batchid', '9999')
        dass.set_assignment('insert', 1, 'special', 'batchid', None, None)
        dass.assign('insert', cur_rec, old_rec, new_rec)
        assert cur_rec == ['a', '9999', 'c', 'd']




class TestComparisonHelpers(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.fqfn     = create_test_file(self.temp_dir)
        self.dialect  = create_dialect(delimiter=',', quoting=csv.QUOTE_NONE, hasheader=False)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_set_fields(self):
        delta         = mod.FileDelta(self.temp_dir, self.dialect)

        delta.set_fields('join', 1)
        assert delta.join_fields == [1]

        delta.set_fields('join', 2)
        assert delta.join_fields == [1,2]

        delta.set_fields('join', 3,4,5)
        assert delta.join_fields == [1,2,3,4,5]

        delta.set_fields('join', '6')
        assert delta.join_fields == [1,2,3,4,5,6]

        delta.set_fields('join', '7,8')
        assert delta.join_fields == [1,2,3,4,5,6,7,8]

#        with pytest.raises(ValueError):
 #           delta.set_fields('join', '6,7')
       

    def test_key_match_equal(self):
        delta         = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0]
        delta.new_rec  = [1,2,3]
        delta.old_rec  = [1,2,3]
        assert delta._key_match() == 'equal'

        delta         = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0,1]
        delta.new_rec  = [1,2,3]
        delta.old_rec  = [1,2,3]
        assert delta._key_match() == 'equal'

        delta         = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0]
        delta.new_rec  = [1]
        delta.old_rec  = [1]
        assert delta._key_match() == 'equal'


    def test_key_match_greater(self):
        delta         = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [1]
        delta.new_rec  = [1,2,3]
        delta.old_rec  = [2,3,4]
        assert delta._key_match() == 'old-greater'

    def test_key_match_lesser(self):
        delta         = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [1]
        delta.new_rec  = [2,3,4]
        delta.old_rec  = [1,2,3]
        assert delta._key_match() == 'new-greater'

    def test_data_match_empty_ignore_fields(self):
        delta           = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [1]
        ignore_fields   = []
        compare_fields  = []
        delta.new_rec   = [1,2,3]
        delta.old_rec   = [1,2,3]
        assert delta._data_match(ignore_fields, compare_fields) is True

        delta           = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [1]
        ignore_fields   = []
        compare_fields  = []
        delta.new_rec   = [1,2,3]
        delta.old_rec   = [1,2,4]
        assert delta._data_match(ignore_fields, compare_fields) is False

    def test_data_match_with_ignore_fields(self):
        delta           = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0]
        ignore_fields   = [1]
        compare_fields  = []
        delta.new_rec   = [1,2,3]
        delta.old_rec   = [1,2,3]
        assert delta._data_match(ignore_fields, compare_fields) is True

        delta           = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0]
        ignore_fields   = [1]
        compare_fields  = []
        delta.new_rec   = [1,2,3]
        delta.old_rec   = [1,2,4] 
        assert delta._data_match(ignore_fields, compare_fields) is False

        delta           = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [0]
        ignore_fields   = [1]
        compare_fields  = [1]
        delta.new_rec   = [1,2,3]
        delta.old_rec   = [1,4,3]  # change should be ignored
        assert delta._data_match(ignore_fields, compare_fields) is True

    def test_data_match_with_compare_fields(self):
        delta             = mod.FileDelta(self.temp_dir, self.dialect)
        delta.join_fields = [1]
        ignore_fields     = []
        compare_fields    = []
        delta.new_rec     = [1,2,3]
        delta.old_rec     = [1,2,3]
        assert delta._data_match(ignore_fields, compare_fields) is True
        compare_fields    = [2]
        assert delta._data_match(ignore_fields, compare_fields) is True
        compare_fields    = [2,3]
        assert delta._data_match(ignore_fields, compare_fields) is True
        delta.old_rec     = [1,9,9]
        compare_fields    = [2]
        assert delta._data_match(ignore_fields, compare_fields) is False








class TestComparison(object):

    def setup_method(self, method):
        self.temp_dir  = tempfile.mkdtemp(prefix='gristle_test_')
        self.old_fqfn  = pjoin(self.temp_dir, 'old.csv')
        self.new_fqfn  = pjoin(self.temp_dir, 'new.csv')
        self.dialect   = create_dialect(delimiter=',', quoting=csv.QUOTE_NONE, hasheader=False)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_1key_empty_file_(self):
        with open(self.old_fqfn, 'w') as f:
            pass
        with open(self.new_fqfn, 'w') as f:
            pass
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 1)
        delta.compare_files(self.old_fqfn, self.new_fqfn)
        assert  os.path.getsize(self.new_fqfn + '.delete') == 0
        assert  os.path.getsize(self.new_fqfn + '.insert') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') == 0
        assert  os.path.getsize(self.new_fqfn + '.same')   == 0

    def test_1key_empty_old_file_(self):
        with open(self.old_fqfn, 'w') as f:
            pass
        with open(self.new_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 0)
        delta.compare_files(self.old_fqfn, self.new_fqfn)
        assert  os.path.getsize(self.new_fqfn + '.delete') == 0
        assert  os.path.getsize(self.new_fqfn + '.insert') > 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') == 0
        assert  os.path.getsize(self.new_fqfn + '.same')   == 0
        insert_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.insert')
        assert insert_rec_cnt == 4

    def test_1key_empty_new_file_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        with open(self.new_fqfn, 'w') as f:
            pass
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 0)
        delta.compare_files(self.old_fqfn, self.new_fqfn)
        assert  os.path.getsize(self.new_fqfn + '.delete') > 0
        assert  os.path.getsize(self.new_fqfn + '.insert') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') == 0
        assert  os.path.getsize(self.new_fqfn + '.same')   == 0
        delete_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.delete')
        assert delete_rec_cnt == 4

    def test_1key_sames_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        with open(self.new_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 0)
        delta.compare_files(self.old_fqfn, self.new_fqfn)
        assert  os.path.getsize(self.new_fqfn + '.delete') == 0
        assert  os.path.getsize(self.new_fqfn + '.insert') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') == 0
        assert  os.path.getsize(self.new_fqfn + '.same')   > 0
        same_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.same')
        assert same_rec_cnt == 4

    def test_1key_oldfile_out_of_order_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('4, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('2, aaa, a23\n')
        with open(self.new_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 1)
        with pytest.raises(SystemExit):
            delta.compare_files(self.old_fqfn, self.new_fqfn)

    def test_1key_newfile_out_of_order_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        with open(self.new_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('4, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('2, aaa, a23\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 1)
        with pytest.raises(SystemExit):
            delta.compare_files(self.old_fqfn, self.new_fqfn)

    def test_2key_sames_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('3, bbb, a23\n')
        with open(self.new_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('3, bbb, a23\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 0)
        delta.compare_files(self.old_fqfn, self.new_fqfn)

        assert  os.path.getsize(self.new_fqfn + '.delete') == 0
        assert  os.path.getsize(self.new_fqfn + '.insert') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') == 0
        assert  os.path.getsize(self.new_fqfn + '.same')   > 0
        same_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.same')
        assert same_rec_cnt == 4

    def test_1key_changes_(self):
        with open(self.old_fqfn, 'w') as f:
            f.write('1, bbb, b23\n')
            f.write('2, bbb, a23\n')
            f.write('3, aaa, b23\n')
            f.write('4, aaa, a23\n')
        with open(self.new_fqfn, 'w') as f:
            f.write('1, ccc, b23\n')
            f.write('2, bbb, b34\n')
            f.write('3, 9,   b23\n')
            f.write('4, aaa, bbb\n')
        delta     = mod.FileDelta(self.temp_dir, self.dialect)
        delta.set_fields('join', 0)
        delta.compare_files(self.old_fqfn, self.new_fqfn)
        assert  os.path.getsize(self.new_fqfn + '.delete') == 0
        assert  os.path.getsize(self.new_fqfn + '.insert') == 0
        assert  os.path.getsize(self.new_fqfn + '.chgnew') > 0
        assert  os.path.getsize(self.new_fqfn + '.chgold') > 0
        assert  os.path.getsize(self.new_fqfn + '.same')   == 0
        chgold_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.chgold')
        assert chgold_rec_cnt == 4
        chgnew_rec_cnt = get_file_rec_cnt(self.new_fqfn + '.chgnew')
        assert chgnew_rec_cnt == 4


def create_test_file(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
            f.write('4, aaa, a23\n')
            f.write('2, bbb, a23\n')
            f.write('1, bbb, b23\n')
            f.write('3, aaa, b23\n')
    return fqfn

def create_sorted_test_file(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
            f.write('4, aaa, a23\n')
            f.write('3, aaa, b23\n')
            f.write('2, bbb, a23\n')
            f.write('1, bbb, b23\n')
    return fqfn

def create_sorted_file_2keys_dups(temp_dir):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
            f.write('4, aaa, a23\n')
            f.write('3, aaa, a23\n')
            f.write('2, bbb, b23\n')
            f.write('1, bbb, b23\n')
    return fqfn

def get_file_rec_cnt(fqfn):
    rec_cnt = 0
    for rec in fileinput.input(fqfn):
        rec_cnt += 1
    return rec_cnt
