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
import subprocess
import pytest
import shutil
import glob
import csv
from pprint  import pprint as pp
from os.path import dirname, basename
from os.path import join as pjoin
import fileinput

import yaml as yaml
import envoy

#--- gristle modules -------------------
import test_tools

# get script_diring set for running code out of project structure & testing it via tox
script_dir   = dirname(dirname(os.path.realpath((__file__))))
sys.path.insert(0, test_tools.get_app_root())

import gristle.common  as comm
import gristle.csvhelper as csvhelp
from gristle.common import dict_coalesce

FIELDS = {'pkid':0, 'vid':1, 'from_epoch':2, 'to_epoch':3, 'foo':4, 'bar':5, 'del_flag':6,
          'gor':7, 'org':8, 'horn':9, 'mook':10, 'hostname':11}


class TestMillionRows(object):
    """ Assumptions:
        - oldfile is from a data warehouse destination
        - newfile is from a transactional source
    """
    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_diff_')
        self.dialect    = csvhelp.create_dialect(',', csvhelp.QUOTE_NONE, False)

        start_time = time.time()
        print '\ncreating test files - starting'
        self.files = CreateTestFiles(1000000, self.temp_dir)
        print 'creating test files - done with duration of %d seconds' % int(time.time() - start_time)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_assign_colname_list(self):
        """
        """
        file1  = pjoin(self.temp_dir, 'old.csv')
        file2  = pjoin(self.temp_dir, 'new.csv')
        config = Config(self.temp_dir)
        config.add_property({'delimiter':','})
        config.add_property({'hasheader':False})
        config.add_property({'quoting':csvhelp.QUOTE_NONE})
        config.add_property({'col_names': sorted(FIELDS, key=FIELDS.get)})
        config.add_property({'key_cols':  ['pkid']})
        config.add_property({'ignore_cols': ['vid','from_epoch','to_epoch','hostname']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'files': [file1, file2]})
        config.add_assignment('delete', 'del_flag',  'literal', 'd',None,None)
        config.add_assignment('delete', 'to_epoch',  'special', 'start_epoch',None, None)
        config.add_assignment('insert', 'from_epoch','special', 'start_epoch',None, None)
        config.add_assignment('insert', 'pkid',      'sequence','',          'old', 'pkid')
        config.add_assignment('insert', 'vid',       'sequence','',          'old', 'vid')
        config.add_assignment('chgold', 'to_epoch',  'special', 'start_epoch',None, None)
        config.add_assignment('chgnew', 'from_epoch','special', 'start_epoch',None, None)
        config.add_assignment('chgnew', 'pkid',      'copy',    '',          'old', 'pkid')
        config.add_assignment('chgnew', 'vid',       'sequence','',          'old', 'vid')
        config.write_config()

        start_time = int(time.time())
        cmd = ''' %s   \
                  --config-fn %s \
                  --variables 'start_epoch:%s'  \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn,
                     start_time)
        r = envoy.run(cmd)
        print r.std_out
        print r.std_err
        print 'running gristle_differ - starting'
        print 'running gristle_differ - done with duration of %d seconds' % int(time.time() - start_time)
        print 'running assertions     - starting'
        self._print_counts()

        #--- first check return code
        assert r.status_code == 0

        #--- next check that the right number of rows got into each file:
        assert get_file_count(pjoin(self.temp_dir, 'new.csv.insert'), self.dialect) == self.files.insert_cnt
        assert get_file_count(pjoin(self.temp_dir, 'new.csv.delete'), self.dialect) == self.files.delete_cnt
        assert get_file_count(pjoin(self.temp_dir, 'new.csv.same'),   self.dialect) == self.files.same_cnt
        assert get_file_count(pjoin(self.temp_dir, 'new.csv.chgold'), self.dialect) == self.files.chg_cnt
        assert get_file_count(pjoin(self.temp_dir, 'new.csv.chgnew'), self.dialect) == self.files.chg_cnt

        #--- next check that the assignments were applied:

        #--- delete file checks ---
        for row in csv.reader(fileinput.input(pjoin(self.temp_dir, 'new.csv.delete')), self.dialect):
            assert row[6] == 'd'              # del_flag
            assert row[3] == str(start_time)  # to_epoch
        fileinput.close()

        #--- insert file checks ---
        ins_pkid_list = []
        ins_vid_list  = []
        min_pkid  = None
        min_vid   = None
        for row in csv.reader(fileinput.input(pjoin(self.temp_dir, 'new.csv.insert')), self.dialect):
            assert row[FIELDS['from_epoch']] == str(start_time)
            ins_pkid_list.append(int(row[FIELDS['pkid']]))
            ins_vid_list.append(int(row[FIELDS['vid']]))
            min_pkid = get_min_id(min_pkid, row[FIELDS['pkid']])
            min_vid  = get_min_id(min_vid, row[FIELDS['vid']])
            assert row[FIELDS['del_flag']] == ''
        fileinput.close()
        assert len(ins_pkid_list) == len(get_uniq_seq(ins_pkid_list))  #ensure there's no duplicate ids
        assert len(ins_vid_list)  == len(get_uniq_seq(ins_vid_list))   #ensure there's no duplicate ids
        assert min_pkid > self.files.old_rec_cnt
        assert min_vid > self.files.old_rec_cnt

        #--- chgold file checks ---
        for row in csv.reader(fileinput.input(pjoin(self.temp_dir, 'new.csv.chgold')), self.dialect):
            assert row[FIELDS['to_epoch']] == str(start_time)
            assert row[FIELDS['del_flag']] == ''
        fileinput.close()

        #--- chgnew file checks ---
        chgnew_vid_list = []
        for row in csv.reader(fileinput.input(pjoin(self.temp_dir, 'new.csv.chgnew')), self.dialect):
            assert row[FIELDS['from_epoch']] == str(start_time)
            assert row[FIELDS['del_flag']] == ''
            chgnew_vid_list.append(int(row[FIELDS['vid']]))
        fileinput.close()
        assert  len(set(ins_vid_list).intersection(chgnew_vid_list)) == 0, 'dup vids across files'

    def _print_counts(self):
        actual_insert_cnt = get_file_count(pjoin(self.temp_dir, 'new.csv.insert'), self.dialect)
        actual_delete_cnt = get_file_count(pjoin(self.temp_dir, 'new.csv.delete'), self.dialect)
        actual_same_cnt   = get_file_count(pjoin(self.temp_dir, 'new.csv.same'), self.dialect)
        actual_chgold_cnt = get_file_count(pjoin(self.temp_dir, 'new.csv.chgold'), self.dialect)
        actual_chgnew_cnt = get_file_count(pjoin(self.temp_dir, 'new.csv.chgnew'), self.dialect)
        print 'inserts - expected: %10d - found: %d' % (self.files.insert_cnt, actual_insert_cnt)
        print 'deletes - expected: %10d - found: %d' % (self.files.delete_cnt, actual_delete_cnt)
        print 'sames   - expected: %10d - found: %d' % (self.files.same_cnt, actual_same_cnt)
        print 'chg     - expected: %10d - found: %d and %d' % (self.files.chg_cnt, actual_chgold_cnt, actual_chgnew_cnt)


def get_min_id(min_id, curr_id):
    try:
        if min_id is None:
            return int(curr_id)
        elif min_id < int(curr_id):
            return int(curr_id)
    except (TypeError, ValueError):
        pytest.fail("Non-integer found in id col")


def get_uniq_seq(seq, userfunc=None):
    if userfunc is None:
        def userfunc(x): return x
    cache  = {}
    result = []
    for el in seq:
        mod_el = userfunc(el)
        if mod_el in cache:
            continue
        cache[mod_el] = 1
        result.append(el)
    return result


def get_file_count(fn, dialect):
    for rec in csv.reader(fileinput.input(fn), dialect=dialect):
        pass
    rec_cnt = fileinput.lineno()
    fileinput.close()
    return rec_cnt



class Config(object):

    def __init__(self, temp_dir):
        self.temp_dir    = temp_dir
        self.config_fqfn = pjoin(temp_dir, 'config.yml')
        self.config      = {}

    def add_property(self, kwargs):
        for key in kwargs:
            #print key
            self.config[key] = kwargs[key]

    def add_assignment(self, dest_file, dest_field, src_type, src_val, src_file, src_field):
        if 'assignments' not in self.config:
            self.config['assignments'] = []
        assignment = {'dest_file':  dest_file,
                      'dest_field': dest_field,
                      'src_type':   src_type,
                      'src_val':    src_val,
                      'src_file':   src_file,
                      'src_field':  src_field}
        self.config['assignments'].append(assignment)

    def write_config(self):
        config_yaml = yaml.safe_dump(self.config)
        with open(self.config_fqfn, 'w') as f:
            f.write(config_yaml)



class CreateTestFiles(object):

    def __init__(self, rec_cnt, temp_dir):

        old_fp = open(pjoin(temp_dir, 'old.csv'), 'w')
        new_fp = open(pjoin(temp_dir, 'new.csv'), 'w')
        self.old_rec_cnt = 0
        self.new_rec_cnt = 0
        self.insert_cnt  = 0
        self.delete_cnt  = 0
        self.chg_cnt     = 0
        self.same_cnt    = 0

        for i in range(rec_cnt):
            r = random.randint(1,100)
            epoch = self._get_epoch(i, r, rec_cnt)
            if self.old_rec_cnt > (rec_cnt * 0.99):
                oldrec, newrec = self._get_insert_recs(i, r, epoch)
                self.insert_cnt += 1
            elif r == 1:
                oldrec, newrec = self._get_delete_recs(i, r, epoch)
                self.delete_cnt += 1
            elif r == 2:
                oldrec, newrec = self._get_chg_recs(i, r, epoch)
                self.chg_cnt += 1
            else:
                oldrec, newrec = self._get_same_recs(i, r, epoch)
                self.same_cnt += 1
            if newrec:
                new_fp.write(newrec)
                self.new_rec_cnt += 1
            if oldrec:
                old_fp.write(oldrec)
                self.old_rec_cnt += 1
        old_fp.close()
        new_fp.close()
        #return (old_rec_cnt, new_rec_cnt, same_cnt, chg_cnt, delete_cnt, insert_cnt)


    def _make_rec(self, **kwargs):
        rec = [''] * len(FIELDS)
        rec[FIELDS['foo']]      = 'foo'
        rec[FIELDS['bar']]      = 'bar'
        rec[FIELDS['gor']]      = 'gor'
        rec[FIELDS['org']]      = 'org'
        rec[FIELDS['horn']]     = 'horn'
        rec[FIELDS['mook']]     = 'mook'
        rec[FIELDS['hostname']] = 'hostname'
        for key in kwargs:
            rec[FIELDS[key]] = str(kwargs[key])
        return ','.join(rec) + '\n'

    def _get_insert_recs(self, pkid, randint, from_epoch):
        newrec = self._make_rec(pkid=pkid)
        return None, newrec

    def _get_delete_recs(self, pkid, randint, from_epoch):
        oldrec = self._make_rec(pkid=pkid, vid=pkid, from_epoch=from_epoch)
        return oldrec, None

    def _get_same_recs(self, pkid, randint, from_epoch):
        oldrec = self._make_rec(pkid=pkid, vid=pkid, from_epoch=from_epoch)
        newrec = self._make_rec(pkid=pkid)
        return oldrec, newrec

    def _get_chg_recs(self, pkid, randint, from_epoch):
        oldrec = self._make_rec(pkid=pkid, vid=pkid, from_epoch=from_epoch )
        newrec = self._make_rec(pkid=pkid, bar='BAR', gor='GOR')
        return oldrec, newrec

    def _get_epoch(self, pkid, rand, tot_recs):
        from_epoch=''
        to_epoch=''
        start_epoch = 1356998400   # 2013-01-01 00:00
        end_epoch   = 1388663940   # 2013-12-31 59:59
        tot_sec     = end_epoch - start_epoch
        interval    = tot_sec / tot_recs
        epoch       = start_epoch + (pkid * interval)
        return epoch








