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

import csv
import glob
import fileinput
import os
from os.path import dirname, basename, isfile
from os.path import join as pjoin
from pprint  import pprint as pp
import shutil
import subprocess
import tempfile

import ruamel.yaml as yaml
import envoy

import datagristle.csvhelper as csvhelper


script_dir = dirname(dirname(os.path.realpath((__file__))))


class TestInvalidInput(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_diff_')
        self.dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_NONE, has_header=False)
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        self.file1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        self.file2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        self.config = Config(self.temp_dir)
        self.config.add_property({'delimiter':'tab'})
        self.config.add_property({'has_header':False})
        self.config.add_property({'quoting':'quote_none'})
        self.config.add_property({'col_names': ['col0', 'col1', 'col2']})
        self.config.add_property({'key_cols': ['0']})
        self.config.add_property({'compare_cols': ['2']})
        self.config.add_property({'temp_dir': self.temp_dir})
        self.config.add_property({'infiles': [self.file1, self.file2]})
        self.config.add_assignment('chgnew', 'col1', 'copy', None, 'old', 'col0')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_assign_colname_list(self):
        """
        """
        # override init values:
        # following entry is invalid: assign field can't be a list:
        self.config.add_assignment('chgnew', ['col1'], 'copy', None, 'old', 'col0')
        self.config.write_config()
        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), self.config.config_fqfn)
        executor(cmd, expect_success=False)


    def test_assign_invalid_colname(self):
        """
        """
        # override init values:
        # following entry is invalid: assign field must be in colname list:
        self.config.add_assignment('chgnew', 'col9', 'copy', None, 'old', 'col0')
        self.config.write_config(valid=False)
        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), self.config.config_fqfn)
        executor(cmd, expect_success=False)


class TestCommandLine(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_diff_')
        self.dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_NONE, has_header=False)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def file_cnt(self, fn, suffix):
        return len(get_file_contents(pjoin(self.temp_dir, fn+suffix), self.dialect))


    def test_easy_files(self):
        """ Objective of this test to is to demonstrate correct processing
            for a pair of simple files.
        """

        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = '''%s  --infiles %s %s -k 0 -c 2 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                                                         fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        assert len(glob.glob(fqfn1)) == 1
        assert len(glob.glob(fqfn2)) == 1
        all_files = glob.glob(pjoin(self.temp_dir, '*'))
        expected_files = [fn2+'.insert', fn2+'.delete', fn2+'.same',
                          fn2+'.chgold', fn2+'.chgnew', fn1,
                          fn2]

        for a_fn in all_files:
            assert basename(a_fn) in expected_files
        assert len(os.listdir(self.temp_dir)) == 7

        insert_list = get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect)
        assert len(insert_list) == 1
        assert insert_list[0][0] == 'new-row'

        delete_list = get_file_contents(pjoin(self.temp_dir, fn2+'.delete'), self.dialect)
        assert len(delete_list) == 1
        assert delete_list[0][0] == 'del-row'

        chgold_list = get_file_contents(pjoin(self.temp_dir, fn2+'.chgold'), self.dialect)
        assert len(chgold_list) == 1
        assert chgold_list[0][0] == 'chg-row'

        chgnew_list = get_file_contents(pjoin(self.temp_dir, fn2+'.chgnew'), self.dialect)
        assert len(chgnew_list) == 1
        assert chgnew_list[0][0] == 'chg-row'

        same_list = get_file_contents(pjoin(self.temp_dir, fn2+'.same'), self.dialect)
        assert len(same_list) == 1
        assert same_list[0][0] == 'same-row'


    def test_empty_new_file(self):
        """
        """
        file1_recs = [['del-row-1', '4', '14'],
                      ['del-row-2', '6', '16'],
                      ['del-row-3', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        file2_recs = []
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        cmd = ''' %s --infiles %s %s -k 0 -c 1 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                                                         fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 0
        assert self.file_cnt(fn2, '.delete') == 3
        assert self.file_cnt(fn2, '.chgold') == 0
        assert self.file_cnt(fn2, '.chgnew') == 0
        assert self.file_cnt(fn2, '.same') == 0


    def test_empty_old_file(self):
        """
        """
        file1_recs = []
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        file2_recs = [['insert-row-1', '4', '14'],
                      ['insert-row-2', '6', '16'],
                      ['insert-row-3', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        cmd = ''' %s --infiles %s %s -k 0 -c 1 --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'),
                                                         fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        assert len(glob.glob(fqfn1)) == 1
        assert len(glob.glob(fqfn2)) == 1
        assert self.file_cnt(fn2, '.insert') == 3
        assert self.file_cnt(fn2, '.delete') == 0
        assert self.file_cnt(fn2, '.chgold') == 0
        assert self.file_cnt(fn2, '.chgnew') == 0
        assert self.file_cnt(fn2, '.same') == 0

    def test_explicit_dialect_pipes_noquotes_noheader(self):
        """
        """
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        # switching to subprocess here because envoy was choking on pipe
        # delimiter
        cmd = [pjoin(script_dir, 'gristle_differ'),
               '--infiles', fqfn1, fqfn2,
               '-k', '0',
               '-c', '2',
               '--delimiter', '|',
               '--quoting', 'quote_none',
               '--has-no-header',
               '--temp-dir', self.temp_dir]
        runner = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = runner.communicate()
        print('------- std_out ------')
        print(stdout)
        print(stderr)

        assert runner.returncode == 0

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1



    def test_explicit_dialect_tabs_noquotes_noheader(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s \
                  -k 0 -c 2 \
                  --delimiter tab --quoting quote_none  --has-no-header \
                  --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'), fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1




    def test_with_args_and_dialect_in_config_file(self):
        """
        """
        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'has_header':False})
        config.write_config()

        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s \
                  -k 0 -c 2 \
                  --config-fn %s \
                  --temp-dir %s''' % (pjoin(script_dir, 'gristle_differ'), fqfn1, fqfn2,
                                      config.config_fqfn, self.temp_dir)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1



    def test_with_config_file_dialect_and_misc_properties(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1



    def test_with_config_file_dialect_and_misc_prop_and_literal_assignment(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.add_assignment('delete', 1, 'literal', 'd', None, None)
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        assert get_file_contents(pjoin(self.temp_dir, fn2+'.delete'),
                                 self.dialect)[0][1] == 'd'

    def test_with_config_file_dialect_and_special_assignment(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14', 'empty'],
                      ['del-row', '6', '16', 'empty'],
                      ['same-row', '8', '18', 'empty']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect,  file1_recs)
        file2_recs = [['chg-row', '4', '1a', 'empty'],
                      ['new-row', '13a', '45b', 'empty'],
                      ['same-row', '8', '18', 'empty']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'variables': ['foo:bar', 'baz:gorilla']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.add_assignment('delete', 1, 'special', 'foo', None, None)
        config.add_assignment('insert', 3, 'special', 'baz', None, None)
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        print(get_file_contents(pjoin(self.temp_dir, fn2+'.delete'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.delete'),
                                 self.dialect)[0][1] == 'bar'
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.insert'),
                                 self.dialect)[0][3] == 'gorilla'

    def test_with_config_file_dialect_and_misc_prop_and_copy_assignment(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.add_assignment('chgnew', 1, 'copy', None, 'old', 0)
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        print(get_file_contents(pjoin(self.temp_dir, fn2+'.delete'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.chgnew'),
                                 self.dialect)[0][1] == 'chg-row'

    def test_with_config_file_dialect_and_misc_prop_and_seq_assignment(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '1'],
                      ['del-row', '6', '2'],
                      ['same-row', '8', '3']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4b', ''],
                      ['new-row', '13a', ''],
                      ['same-row', '8', '']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['1']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        #config.add_assignment('insert',1,'sequence',None,'old',2)
        config.add_assignment('insert', 2, 'sequence', None, 'old', 2)
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        print('get file contents - insert: ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect))
        print('get file contents - delete: ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.delete'), self.dialect))
        print('get file contents - same ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.same'), self.dialect))
        print('get file contents - chgold ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.chgold'), self.dialect))
        print('get file contents - chgnew ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.chgnew'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect)[0][2] == '4'

    def test_with_seq_assignment_based_on_arg_var(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', ''],
                      ['del-row', '6', ''],
                      ['same-row', '8', '']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        file2_recs = [['chg-row', '4b', ''],
                      ['new-row', '13a', ''],
                      ['same-row', '8', '']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['1']})
        config.add_property({'variables': ['foo:7']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.add_assignment('insert', 2, 'sequence', 'foo', None, None)
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        print('get file contents - insert: ')
        print(get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.insert'), self.dialect)[0][2] == '8'

    def test_with_multi_cols(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14', 'foo'],
                      ['del-row', '6', '16', 'foo'],
                      ['same-row', '8', '18', 'bar']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a', 'foo'],
                      ['new-row', '13a', '45b', 'baz'],
                      ['same-row', '8', '18', 'bar']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'key_cols': ['0', '1']})
        config.add_property({'compare_cols': ['2', '3']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1


    def test_colnames_for_keycol_and_comparecol(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'col_names': ['col0', 'col1', 'col2']})
        config.add_property({'key_cols': ['col0']})
        config.add_property({'compare_cols': ['col2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1


    def test_colnames_and_colnum_mix_for_ignorecol(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14', 'same'],
                      ['del-row', '6', '16', 'same'],
                      ['same-row', '8', '18', 'same']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a', 'same'],
                      ['new-row', '13a', '45b', 'same'],
                      ['same-row', '8', '18', 'same']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'col_names': ['col0', 'col1', 'col2', 'col3']})
        config.add_property({'key_cols': ['col0']})
        config.add_property({'ignore_cols': ['col1', 3]})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)

        assert self.file_cnt(fqfn2, '.insert') == 1
        assert self.file_cnt(fqfn2, '.delete') == 1
        assert self.file_cnt(fqfn2, '.chgold') == 1
        assert self.file_cnt(fqfn2, '.chgnew') == 1
        assert self.file_cnt(fqfn2, '.same') == 1


    def test_colname_copy_assignment(self):
        """
        """
        self.dialect.delimiter = '\t'
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)

        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)

        config = Config(self.temp_dir)
        config.add_property({'delimiter':'tab'})
        config.add_property({'has_header':False})
        config.add_property({'quoting':'quote_none'})
        config.add_property({'col_names': ['col0', 'col1', 'col2']})
        config.add_property({'key_cols': ['0']})
        config.add_property({'compare_cols': ['2']})
        config.add_property({'temp_dir': self.temp_dir})
        config.add_property({'infiles': [fqfn1, fqfn2]})
        config.add_assignment('chgnew', 'col1', 'copy', None, 'old', 'col0')
        config.write_config()

        cmd = ''' %s   \
                  --config-fn %s \
              ''' % (pjoin(script_dir, 'gristle_differ'), config.config_fqfn)
        executor(cmd)
        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1

        print(get_file_contents(pjoin(self.temp_dir, fn2+'.delete'), self.dialect))
        assert get_file_contents(pjoin(self.temp_dir, fn2+'.chgnew'), self.dialect)[0][1] == 'chg-row'


    def test_option_already_sorted(self):
        """
        """
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s \
                 --infiles %s %s \
                 -k 0 -c 2 --temp-dir %s\
                 --already-sorted''' % (pjoin(script_dir, 'gristle_differ'),
                                        fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1


    def test_option_already_uniq(self):
        """
        """
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16'],
                      ['same-row', '8', '18']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b'],
                      ['same-row', '8', '18']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s \
                  -k 0 -c 2 --temp-dir %s \
                  --already-uniq''' % (pjoin(script_dir, 'gristle_differ'),
                                       fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        pp(os.listdir(self.temp_dir))
        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 1


    def test_option_stats(self):
        """
        """
        file1_recs = [['chg-row', '4', '14'],
                      ['del-row', '6', '16']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s \
                  -k 0 -c 2 --temp-dir %s --verbosity high''' % (pjoin(script_dir, 'gristle_differ'),
                                                                 fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        pp(os.listdir(self.temp_dir))
        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same') == 0


    def test_option_column_names_default(self):
        """
        Note that header records are not skipped, but can get used for column_names
        """
        file1_recs = [['rowkey' , 'col1', 'col2'],
                      ['chg-row', '4', '14'],
                      ['del-row', '6', '16']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['rowkey' , 'col1', 'col2'],
                      ['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s
                  --infiles %s %s
                  --verbosity debug
                  --has-header
                  -k rowkey -c col2 --temp-dir %s  ''' % (pjoin(script_dir, 'gristle_differ'),
                                                          fqfn1, fqfn2, self.temp_dir)
        executor(cmd)

        print('file1: ')
        os.system(f'cat {fqfn1}')
        print('\nfile2: ')
        os.system(f'cat {fqfn2}')
        print('')

        pp(os.listdir(self.temp_dir))
        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same')   == 0 # the header is the same, but it won't get counted


    def test_option_column_names_explicit(self):
        """
        Note that header records are not skipped, but can get used for column_names
        """
        file1_recs = [['badkey' , 'badcol1', 'badcol2'],
                      ['chg-row', '4', '14'],
                      ['del-row', '6', '16']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['badkey' , 'badcol1', 'badcol2'],
                      ['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s \
                  -k rowkey -c col2 --temp-dir %s  --col-names rowkey col1 col2   ''' \
            % (pjoin(script_dir, 'gristle_differ'), fqfn1, fqfn2, self.temp_dir)

        executor(cmd)

        print('file1: ')
        os.system(f'cat {fqfn1}')
        print('\nfile2: ')
        os.system(f'cat {fqfn2}')
        print('')

        pp(os.listdir(self.temp_dir))
        assert self.file_cnt(fn2, '.insert') == 1
        assert self.file_cnt(fn2, '.delete') == 1
        assert self.file_cnt(fn2, '.chgold') == 1
        assert self.file_cnt(fn2, '.chgnew') == 1
        assert self.file_cnt(fn2, '.same')   == 0 # the header won't be counted


    def test_missing_key_cols(self):
        """
        """
        file1_recs = [['badkey' , 'badcol1', 'badcol2'],
                      ['chg-row', '4', '14'],
                      ['del-row', '6', '16']]
        fqfn1 = generate_test_file(self.temp_dir, 'old_', '.csv', self.dialect, file1_recs)
        fn1 = basename(fqfn1)
        file2_recs = [['badkey' , 'badcol1', 'badcol2'],
                      ['chg-row', '4', '1a'],
                      ['new-row', '13a', '45b']]
        fqfn2 = generate_test_file(self.temp_dir, 'new_', '.csv', self.dialect, file2_recs)
        fn2 = basename(fqfn2)
        assert isfile(fqfn1)
        assert isfile(fqfn2)

        cmd = ''' %s \
                  --infiles %s %s -c 2 --temp-dir %s  ''' \
            % (pjoin(script_dir, 'gristle_differ'), fqfn1, fqfn2, self.temp_dir)

        executor(cmd, expect_success=False)





def executor(cmd, expect_success=True):
    runner = envoy.run(cmd)
    print(runner.std_out)
    print(runner.std_err)
    if expect_success:
        assert runner.status_code == 0
    else:
        assert runner.status_code != 0



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
        pp(rec)
    fp.close()
    return fqfn



class Config(object):

    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.config_fqfn = pjoin(temp_dir, 'config.yml')
        self.config = {}

    def add_property(self, kwargs):
        for key in kwargs:
            print(key)
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

    def write_config(self, valid=True):
        config_yaml = yaml.safe_dump(self.config)
        print(config_yaml)
        with open(self.config_fqfn, 'w') as f:
            f.write(config_yaml)
        # uncomment this code to capture copies of all valid configs
        #if valid == True:
        #    for i in range(50):
        #        bkup_config_fn = '/tmp/test_config_%d.yml' % i
        #        if not isfile(bkup_config_fn):
        #            break
        #    os.system('cp %s %s' % (self.config_fqfn, bkup_config_fn))

