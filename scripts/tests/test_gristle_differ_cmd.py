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

# get script_diring set for running code out of project structure & testing it via
# tox
#script_dir = dirname(dirname(os.path.realpath((__file__))))
#data_dir    = pjoin(test_tools.get_app_root(), 'data')
script_dir   = dirname(dirname(os.path.realpath((__file__))))
#fq_pgm       = pjoin(script_dir, 'gristle_differ')
sys.path.insert(0, test_tools.get_app_root())

import gristle.common  as comm
import gristle.csvhelper as csvhelp
from gristle.common import dict_coalesce








class TestCommandLine(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_diff_')
        self.fieldnames = ['col-key', 'col-1', 'col-2']
        self.dialect    = csvhelp.create_dialect('|', csvhelp.QUOTE_NONE, False)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_easy_files(self):
        """ Objective of this test to is to demonstrate correct processing
            for a pair of simple files.
        """

        file1_recs = [ ['chg-row','4','14'],
                       ['del-row','6','16'],
                       ['same-row','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [ ['chg-row','4','1a'],
                       ['new-row','13a','45b'],
                       ['same-row','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 2 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                 file1, file2, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err
        assert r.status_code == 0

        assert len(glob.glob(file1)) == 1
        assert len(glob.glob(file2)) == 1
        all_files = glob.glob(pjoin(self.temp_dir, '*'))
        fn = basename(file2)
        expected_files = [fn+'.insert', fn+'.delete', fn+'.same',
                          fn+'.chgold', fn+'.chgnew', basename(file1),
                          basename(file2)]

        for a_fn in all_files:
            assert basename(a_fn) in expected_files
        assert len(os.listdir(self.temp_dir)) == 7

        insert_list = get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect)
        assert len(insert_list) == 1
        assert insert_list[0][0] == 'new-row'

        delete_list = get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect)
        assert len(delete_list) == 1
        assert delete_list[0][0] == 'del-row'

        chgold_list = get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect)
        assert len(chgold_list) == 1
        assert chgold_list[0][0] == 'chg-row'

        chgnew_list = get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect)
        assert len(chgnew_list) == 1
        assert chgnew_list[0][0] == 'chg-row'

        same_list = get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect)
        assert len(same_list) == 1
        assert same_list[0][0] == 'same-row'


    def test_empty_new_file(self):
        """ 
        """
        file1_recs = [ ['del-row-1','4','14'],
                       ['del-row-2','6','16'],
                       ['del-row-3','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [ ]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 1 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                 file1, file2, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err

        assert r.status_code == 0
        fn = basename(file2)
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 3 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_empty_old_file(self):
        """
        """
        file1_recs = [ ]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [ ['insert-row-1','4','14'],
                       ['insert-row-2','6','16'],
                       ['insert-row-3','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 1 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                 file1, file2, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err

        assert r.status_code == 0
        assert len(glob.glob(file1)) == 1
        assert len(glob.glob(file2)) == 1
        fn = basename(file2)
        assert 3 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 0 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_explicit_dialect_pipes_noquotes_noheader(self):
        """
        """
        file1_recs = [ ['chg-row','4','14'],
                       ['del-row','6','16'],
                       ['same-row','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [ ['chg-row','4','1a'],
                       ['new-row','13a','45b'],
                       ['same-row','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 2 \
                  --delimiter '|' --quoting quote_none  --hasnoheader \
                  --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                 file1, file2, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err

        assert r.status_code == 0
        fn = basename(file2)
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_explicit_dialect_tabs_noquotes_noheader(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [ ['chg-row','4','14'],
                       ['del-row','6','16'],
                       ['same-row','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [ ['chg-row','4','1a'],
                       ['new-row','13a','45b'],
                       ['same-row','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 2 \
                  --delimiter tab --quoting quote_none  --hasnoheader \
                  --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'), file1, file2, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err

        assert r.status_code == 0
        fn = basename(file2)
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_with_args_and_dialect_in_config_file(self):
        """
        """
        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'quoting':csvhelp.QUOTE_NONE})
        config.add_property({'hasheader':False})
        config.write_config()

        self.dialect.delimiter = '\t'
        file1_recs = [ ['chg-row','4','14'],
                       ['del-row','6','16'],
                       ['same-row','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [ ['chg-row','4','1a'],
                       ['new-row','13a','45b'],
                       ['same-row','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        cmd = ''' %s %s %s -k 0 -c 2 \
                  --config-fn %s \
                  --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'), file1, file2,
                                      config.config_fqfn, self.temp_dir)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err
        assert r.status_code == 0
        fn = basename(file2)

        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_with_config_file_dialect_and_misc_properties(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [ ['chg-row','4','14'],
                       ['del-row','6','16'],
                       ['same-row','8','18']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [ ['chg-row','4','1a'],
                       ['new-row','13a','45b'],
                       ['same-row','8','18']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'hasheader':False})
        config.add_property({'quoting':csvhelp.QUOTE_NONE})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'files': [file1, file2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err
        assert r.status_code == 0
        fn = basename(file2)
        for rec in r.std_out:
            print rec

        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))


    def test_with_multi_cols(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [ ['chg-row','4','14','foo'],
                       ['del-row','6','16','foo'],
                       ['same-row','8','18','bar']]
        file1    = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [ ['chg-row','4','1a','foo'],
                       ['new-row','13a','45b','baz'],
                       ['same-row','8','18','bar']]
        file2    = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'hasheader':False})
        config.add_property({'quoting':csvhelp.QUOTE_NONE})
        config.add_property({'key_cols': ['0', '1']})
        config.add_property({'compare_cols': ['2','3']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'files': [file1, file2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        r = envoy.run(cmd)
        print '------- std_out ------'
        print r.std_out
        print r.std_err
        assert r.status_code == 0
        fn = basename(file2)
        for rec in r.std_out:
            print rec

        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.insert'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.delete'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgold'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.chgnew'), self.dialect))
        assert 1 == len(get_file_contents(pjoin(self.temp_dir, fn+'.same'), self.dialect))

    def notest_multi_column(self):
        """ Tests ability to specify multiple key or comparison columns
            TBD
        """
        pass

    def notest_maxsize(self):
        """ Tests with files greater than maxsize and tests overriding of maxsize
            TBD
        """
        pass

    def notest_dialect_overrides(self):
        """ Tests hasheader, delimiter, and recdelimiter args
            TBD
        """
        pass

    def notest_counts(self):
        """ diff cmdline: Tests counts
            TBD
        """
        pass


def get_file_contents(fn, dialect):
    recs = []
    for rec in csv.reader(fileinput.input(fn), dialect=dialect):
        recs.append(rec)
    return recs


def generate_test_file(temp_dir, pre, suf, dialect, rec_list):
    (fd, fqfn) = tempfile.mkstemp(dir=temp_dir, prefix=pre, suffix=suf)
    fp = os.fdopen(fd,"w")
    for rec in rec_list:
        fp.write(dialect.delimiter.join(rec)+'\n')
    fp.close()
    return fqfn


class Config(object):

    def __init__(self, temp_dir):
        self.temp_dir    = temp_dir
        self.config_fqfn = pjoin(temp_dir, 'config.yml')
        self.config      = {}

    def add_property(self, kwargs):
        for key in kwargs:
            print key
            self.config[key] = kwargs[key]

    def add_assignment(self, dest_file, dest_field, src_type, src_val, src_file, src_field):
        if 'assignments' not in self.config:
            self.config['assignments'] = []
            assignment = {'dest_file': dest_file, 'dest_field': dest_field,
                          'src_type':  src_type,  'src_val':    src_val,
                          'src_file':  src_file,  'src_field':  src_field}
            self.config['assignments'].append(assignment)

    def write_config(self):
        config_yaml = yaml.safe_dump(self.config)
        with open(self.config_fqfn, 'w') as f:
            f.write(config_yaml)










