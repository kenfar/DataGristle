#!/usr/bin/env python
""" This harness provides Functional Tests for gristle_dir_merger.  That is,
    it runs the entire application rather than just testing specific classes 
    or functions.

    Usage instructions: run with pytest:
        $ py.test <this file>

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2014 Ken Farmer
"""

import sys
import os
import tempfile
import time
import fileinput
import pytest
import glob
import errno
import shutil
from pprint import pprint as pp

import envoy
import yaml

#--- gristle modules -------------------
import test_tools as tt

# get pathing set for running code out of project structure & testing it via tox
data_dir    = os.path.join(tt.get_app_root(), 'data')
script_dir  = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))
PGM         = os.path.join(script_dir, 'gristle_dir_merger')
sys.path.insert(0, tt.get_app_root())

import gristle.common  as comm
from gristle.common import dict_coalesce

def rmtree_ignore_error(path):
    """ Have to do this a lot, moving this into a function to save lines of code.
        ignore_error=True should work, but doesn't.
    """
    try:
        shutil.rmtree(path)
    except OSError:
        pass

class TestEmpties(object):
    """ Tests gristle_dir_merger when used with empty directoreis.
    """

    def setup_method(self, method):

        self.source_dir = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.dest_dir   = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')

    def teardown_method(self, method):
        rmtree_ignore_error(self.source_dir)
        shutil.rmtree(self.dest_dir)

    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

    def test_empty_to_empty(self):

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         --match-on-name-only      \
                         --log-level debug         \
                         -r                        \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0

    def test_nonempty_to_empty(self):

        tt.touch(os.path.join(self.source_dir, 'foo.csv'))

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         --match-on-name-only      \
                         --log-level debug         \
                         -r                        \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'foo.csv' in os.listdir(self.dest_dir)
        assert not os.path.exists(self.source_dir)


    def test_nonempty_subdir_to_empty(self):
        """      starting dirs & files:
            \tmp\TestGristleDirMerger_source_?\mysubdir
            \tmp\TestGristleDirMerger_source_?\mysubdir\foo.csv
            \tmp\TestGristleDirMerger_dest_?
                  should become:
            \tmp\TestGristleDirMerger_source_?
            \tmp\TestGristleDirMerger_dest_?\mysubdir\foo.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')

        subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(subdir)
        tt.touch(os.path.join(subdir, 'foo.csv'))

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         --match-on-name-only      \
                         --log-level debug         \
                         -r                        \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        print 'dest_dir: %s' % self.dest_dir
        print os.listdir(self.dest_dir)
        print 'dest sub dir: %s' % os.path.join(self.dest_dir, 'mysubdir')
        print 'dest sub contents: '
        #print os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        print 'is a file? %s' % os.path.isfile(os.path.join(self.dest_dir, 'mysubdir'))

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert not os.path.exists(self.source_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))




class TestMatchOnNameOnly(object):
    """ Tests gristle_dir_merger with criteria of name only.
    """

    def setup_method(self, method):
        self.source_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(self.source_subdir)

        self.dest_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')
        self.dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(self.dest_subdir)

        create_test_file(self.source_subdir, 'foo.csv', '', 2012)


    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)


    def assert_results(self, envoy_result, source_files=None, dest_files=None,
                       source_subdir_exists=False):

        print_outputs(envoy_result)
        assert_results(envoy_result, self.source_dir, self.dest_dir,
                       source_files, dest_files, source_subdir_exists)

    def test_unique_files_and_onmatch_is_useboth(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\bar.csv
                  should become:
            dst_dir\mysubdir\foo.csv
            dst_dir\mysubdir\bar.csv
        """
        create_test_file(self.dest_subdir, 'bar.csv', '')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_both')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'bar.csv'])

    def test_dup_files_and_onmatch_is_useboth(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.csv
                  should become:
            dst_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.1.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', '')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_both')
        r = envoy.run(self.cmd)
        print('dest_dir:')
        print(os.listdir(self.dest_dir))
        print('')
        print('dest_subdir:')
        print(os.listdir(self.dest_subdir))
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])

    def test_dup_files_and_onmatch_is_usesource(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.csv
                  should become:
            dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', final_contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_source')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert '' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usedest(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.csv
                  should become:
            dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_dest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usebiggest(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.csv
                  should become:
            dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_biggest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usenewest(self):
        """      starting dirs & files:
            src_dir\mysubdir\foo.csv
            dst_dir\mysubdir\foo.csv
                  should become:
            dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different', year=2014)
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_only', on_match='keep_newest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))


class TestMatchOnAndMD5(object):
    """ Tests gristle_dir_merger with criteria of name and md5.
    """

    def setup_method(self, method):
        self.source_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(self.source_subdir)

        self.dest_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')
        self.dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(self.dest_subdir)

        create_test_file(self.source_subdir, 'foo.csv', '', 2012)


    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)


    def assert_results(self, envoy_result, source_files=None, dest_files=None,
                       source_subdir_exists=False):

        print_outputs(envoy_result)
        assert_results(envoy_result, self.source_dir, self.dest_dir,
                       source_files, dest_files, source_subdir_exists)

    def test_unique_files_and_onmatch_is_useboth(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\bar.csv
            should become:
                dst_dir\mysubdir\foo.csv
                dst_dir\mysubdir\bar.csv
        """
        create_test_file(self.dest_subdir, 'bar.csv', '')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'bar.csv'])

    def test_dup_files_and_onmatch_is_useboth_with_fullmatch(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.1.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', '')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])

    def test_dup_files_and_onmatch_is_useboth_with_partialmatch(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.1.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', 'im-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])

    def test_dup_files_and_onmatch_is_usesource_with_partialmatch(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', final_contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_source')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert '' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usedest_with_partialmatch(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_dest', on_partial_match='keep_dest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usebiggest_with_partialmatch(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_biggest', on_partial_match='keep_biggest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_dup_files_and_onmatch_is_usenewest_with_partial_match(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.csv
            should become:
                dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='is-different', year=2014)
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_newest', on_partial_match='keep_newest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert 'is-different' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))


class TestMatchOnNameAndMd5Extras(object):
    """ Tests gristle_dir_merger with criteria of name only.
    """

    def setup_method(self, method):

        self.source_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(self.source_subdir)

        self.dest_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')
        self.dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(self.dest_subdir)

        create_test_file(self.source_subdir, 'foo.csv', '', 2012)


    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)

    def get_outputs(self, response):
        print ' '.join(response.command)
        print response.status_code
        print response.std_out
        print response.std_err

    def assert_results(self, envoy_result, source_files=None, dest_files=None,
                       source_subdir_exists=False):

        print_outputs(envoy_result)
        assert_results(envoy_result, self.source_dir, self.dest_dir,
                       source_files, dest_files, source_subdir_exists)


    def test_basics_unique_names_in_a_new_subdir(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv
                dst_dir
            should become:
                dst_dir\mysubdir\foo.csv
        """
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_dest', on_partial_match='keep_newest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])


    def test_files_with_same_md5sums(self):
        """starting dirs & files:
              src_dir\mysubdir\foo.csv
              dst_dir\mysubdir\foo.csv
           should become:
              dst_dir\mysubdir\foo.csv
        """
        create_test_file(self.dest_subdir, 'foo.csv', contents='', year=2014)

        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_dest', on_partial_match='keep_newest')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])

    def test_big_files_with_same_size_but_diff_md5_and_useboth(self):
        """ starting dirs & files:
                src_dir\mysubdir\foo.csv        # file moved
                dst_dir\mysubdir\foo.csv
             should become:
                dst_dir\mysubdir\foo.csv
                dst_dir\mysubdir\foo.1.csv      # (action=keep_both)
        """
        shutil.rmtree(self.source_dir)
        self.source_dir  = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        source_subdir    = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        create_test_file(source_subdir, 'foo.csv', records=10000)  #mostly same

        create_test_file(self.dest_subdir, 'foo.csv',   records=10000,
                         last_row_odd=True)    #mostly same

        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')
        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])


class TestActionUseBoth(object):
    """ Tests gristle_dir_merger with action of keep_newest.
        starting dirs & files:
            \tmp\*_source_?\mysubdir
            \tmp\*_source_?\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv
        should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir\foo.1.csv
    """

    def setup_method(self, method):
        self.source_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(self.source_subdir)

        self.dest_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')
        self.dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(self.dest_subdir)

        create_test_file(self.source_subdir, 'foo.csv', '')

    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)

    def print_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

    def assert_results(self, envoy_result, source_files=None, dest_files=None,
                       source_subdir_exists=False):

        self.print_outputs(envoy_result)
        assert_results(envoy_result, self.source_dir, self.dest_dir,
                       source_files, dest_files, source_subdir_exists)


    def test_matchon_nameandmd5_with_full_match(self):

        create_test_file(self.dest_subdir, 'foo.csv', final_contents='')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])

    def test_matchon_nameandmd5_with_partial_match(self):

        create_test_file(self.dest_subdir, 'foo.csv', final_contents='foobear')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'foo.1.csv'])

    def test_matchon_nameandmd5_with_partial_match_source(self):

        create_test_file(self.dest_subdir, 'foo.csv', final_contents='foobear')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_source')

        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv'])
        assert '' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))

    def test_matchon_nameandmd5_with_partial_match_nomatch(self):

        create_test_file(self.dest_subdir, 'bar.csv', final_contents='foobear')
        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r, source_files=None, dest_files=['foo.csv', 'bar.csv'])


class TestOnSymLinks(object):
    """ Tests gristle_dir_merger with action of keep_newest.
        starting dirs & files:
            \tmp\*_source_?\mysubdir
            \tmp\*_source_?\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv
        should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir\foo.1.csv
    """

    def setup_method(self, method):
        self.source_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(self.source_subdir)

        self.real_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_real_')

        self.dest_dir    = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')
        self.dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(self.dest_subdir)

        create_test_file(self.source_subdir, 'foo.csv', '')

    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)

    def print_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

    def assert_results(self, envoy_result, source_files=None, dest_files=None,
                       source_subdir_exists=False):

        self.print_outputs(envoy_result)
        assert_results(envoy_result, self.source_dir, self.dest_dir,
                       source_files, dest_files, source_subdir_exists,
                       expected_status_code=1)


    def test_symbolic_source_dir(self):

        self.fake_source_dir = os.path.join(self.real_dir, 'myfakedir')
        os.symlink(self.source_subdir, self.fake_source_dir)

        create_test_file(self.source_subdir, 'foo.csv', final_contents='')
        create_test_file(self.dest_subdir, 'foo.csv', final_contents='')

        self.cmd = get_cmd(self.fake_source_dir, self.dest_dir,
                   match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r)

    def test_symbolic_dest_dir(self):

        self.fake_dest_dir = os.path.join(self.real_dir, 'myfakedir')
        #os.symlink(self.dest_subdir, self.fake_dest_dir)
        os.symlink(self.dest_dir, self.fake_dest_dir)

        create_test_file(self.source_subdir, 'foo.csv', final_contents='')
        create_test_file(self.dest_subdir, 'foo.csv', final_contents='')

        self.cmd = get_cmd(self.source_dir, self.fake_dest_dir,
                   match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r)


    def test_symbolic_source_dir(self):

        self.fake_source_dir = os.path.join(self.real_dir, 'myfakedir')
        os.symlink(self.source_dir, self.fake_source_dir)

        create_test_file(self.source_subdir, 'foo.csv', final_contents='')
        create_test_file(self.dest_subdir, 'foo.csv', final_contents='')

        self.cmd = get_cmd(self.fake_source_dir, self.dest_dir,
                   match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r)


    def test_symbolic_source_file(self):

        create_test_file(self.real_dir, 'foo.csv', final_contents='')
        os.symlink(os.path.join(self.real_dir, 'foo.csv'),
                   os.path.join(self.source_subdir, 'foo_fake.csv'))

        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                   match_on='name_and_md5', on_match='keep_both', on_partial_match='keep_both')

        r = envoy.run(self.cmd)
        self.assert_results(r)


class TestDryRun(object):
    """ Tests gristle_dir_merger with criteria of name only.
    """

    def setup_method(self, method):
        self.source_dir = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.dest_dir   = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')

    def teardown_method(self, method):
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.dest_dir)

    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

    def test_nonempty_subdir_to_nonempty_dir(self):
        """      starting dirs & files:
            \tmp\TestGristleDirMerger_source_?\mysubdir
            \tmp\TestGristleDirMerger_source_?\mysubdir\foo.csv
            \tmp\TestGristleDirMerger_dest_???\mysubdir\bar.csv
                  should become:
            \tmp\TestGristleDirMerger_source_?
            \tmp\TestGristleDirMerger_source_?\mysubdir\foo.csv
            \tmp\TestGristleDirMerger_dest_???\mysubdir\bar.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        tt.touch(os.path.join(source_subdir, 'foo.csv'))

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        tt.touch(os.path.join(dest_subdir, 'bar.csv'))


        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         --match-on-name-only      \
                         --dry-run                 \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'bar.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' in os.listdir(self.source_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.source_dir, 'mysubdir'))


class TestDeepDirectory(object):
    """ Tests gristle_dir_merger with action of keep_newest.
    """

    def setup_method(self, method):
        self.source_dir = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.dest_dir   = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')

    def teardown_method(self, method):
        shutil.rmtree(self.dest_dir)
        rmtree_ignore_error(self.source_dir)

    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

    def test_basics(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir
            \tmp\*_source_?\mysubdir\foo
            \tmp\*_source_?\mysubdir\foo\foo.csv
            \tmp\*_source_?\mysubdir\foo\foo2
            \tmp\*_source_?\mysubdir\foo\foo2\foo2.csv
            \tmp\*_source_?\mysubdir\foo\foo2\foo3
            \tmp\*_source_?\mysubdir\foo\foo2\foo3\foo3.csv
            \tmp\*_dest_???\mysubdir\foo
            \tmp\*_dest_???\mysubdir\foo\foo.csv
            \tmp\*_dest_???\mysubdir\foo\foo2
            \tmp\*_dest_???\mysubdir\foo\foo2\foo3
            \tmp\*_dest_???\mysubdir\foo\foo2\foo3\foo3.csv
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo
            \tmp\*_dest_???\mysubdir\foo\foo.csv
            \tmp\*_dest_???\mysubdir\foo\foo2
            \tmp\*_dest_???\mysubdir\foo\foo2\foo2.csv
            \tmp\*_dest_???\mysubdir\foo\foo2\foo3
            \tmp\*_dest_???\mysubdir\foo\foo2\foo3\foo3.csv
        """

        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        foo_subdir = os.path.join(source_subdir, 'foo')
        os.mkdir(foo_subdir)
        create_test_file(foo_subdir, 'foo.csv', '')
        foo2_subdir = os.path.join(foo_subdir, 'foo2')
        os.mkdir(foo2_subdir)
        create_test_file(foo2_subdir, 'foo2.csv', '')
        foo3_subdir = os.path.join(foo2_subdir, 'foo3')
        os.mkdir(foo3_subdir)
        create_test_file(foo3_subdir, 'foo3.csv', '')

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        foo_subdir = os.path.join(dest_subdir, 'foo')
        os.mkdir(foo_subdir)
        create_test_file(foo_subdir, 'foo.csv', '')
        foo2_subdir = os.path.join(foo_subdir, 'foo2')
        os.mkdir(foo2_subdir)
        create_test_file(foo2_subdir, 'foo2.csv', '')
        foo3_subdir = os.path.join(foo2_subdir, 'foo3')
        os.mkdir(foo3_subdir)
        create_test_file(foo3_subdir, 'foo3.csv', '')

        self.cmd = get_cmd(self.source_dir, self.dest_dir,
                           match_on='name_and_md5', on_match='keep_dest', on_partial_match='keep_dest')

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        #assert 'mysubdir'   not in os.listdir(self.source_dir)
        assert not os.path.exists(self.source_dir)
        assert 'mysubdir'   in os.listdir(self.dest_dir)
        assert 'foo'        in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'foo.csv'    in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo'))
        assert 'foo2'       in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo'))
        assert 'foo2.csv'   in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2'))
        assert 'foo3'       in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2'))
        assert 'foo3.csv'   in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2', 'foo3'))



def create_test_file(path, file_name,
                     contents='blahblahblahfidoblahblah\n',
                     year=None,
                     records=1,
                     final_contents=None,
                     last_row_odd=False):
    """ Inputs:
           - path
           - file_name
           - contents - defaults to 'blahblahblahfidoblahblah\n'
           - year - defaults to None, if provided it will change the mtime of the file
             to this year
           - records - defaults to 1, will write the content this many times
           - final_contents - defaults to None, will write this at the end of the file.
             Useful when you want to make two big files and one slightly different.
           - last_row_odd - defaults to False, will cause the last row to be an alternate
             value of the exact same length.
        Returns:
           - Nothing
    """

    fp = open(os.path.join(path, file_name),"w")
    for i in range(records):
        if last_row_odd and i == (records-1):
            odd_contents = contents.swapcase()
            fp.write(odd_contents)
        else:
            fp.write(contents)
    if final_contents:
        fp.write('%s\n' % final_contents)
    fp.close()

    if year:
        t = time.mktime(time.strptime('01.01.%d 00:00:00' % year, '%d.%m.%Y %H:%M:%S'))
        os.utime(os.path.join(path, file_name), (t, t))



def get_file_contents(fqfn):
    with open(fqfn, 'r') as f:
        return f.read()


def get_file_myear(fqfn):
    filemtime = os.path.getmtime(fqfn)
    return int(time.strftime('%Y', time.localtime(filemtime)))


def get_cmd(source_dir, dest_dir, match_on, on_match, on_partial_match=None):

        pgm      = PGM
        if match_on == 'name_only':
            mo_opt = '--match-on-name-only'
        else:
            mo_opt = '--match-on-name-and-md5'
        if on_partial_match is None:
            opm_opt = ''
        else:
            opm_opt = '--on-partial-match %s' % on_partial_match
        cmd  = """%(pgm)s %(source_dir)s                      \
                          %(dest_dir)s                        \
                     %(mo_opt)s                               \
                     --on-full-match     %(on_match)s         \
                     %(opm_opt)s                              \
                     --log-level         debug                \
                     -r                                       \
               """ % locals()
        print '\n command: %s' % cmd
        return cmd


def assert_results(env_result, source_dir, dest_dir, source_files=None, dest_files=None, source_subdir_exists=False,
                   expected_status_code=0):
    assert env_result.status_code      == expected_status_code
    assert 'mysubdir'   in os.listdir(dest_dir)

    if env_result.status_code == 0:
        if source_subdir_exists:
            assert 'mysubdir'   in os.listdir(source_dir)
            # assert all files in my source_files list actually exist:
            for sfile in source_files:
                assert sfile in os.listdir(os.path.join(source_dir, 'mysubdir'))
            # assert all actual source files are in my source_file list:
            for sfile in os.listdir(os.path.join(source_dir, 'mysubdir')):
                assert sfile in source_files
        else:
            assert source_files == None, "Bad test args"
            #assert 'mysubdir'   not in os.listdir(source_dir)
            assert not os.path.exists(source_dir)

    # assert all files in my dest_files list actually exist:
    if dest_files:
        for dfile in dest_files:
            assert dfile in os.listdir(os.path.join(dest_dir, 'mysubdir'))
    # assert all actual dest files are in my dest_file list:
    if dest_files:
        for dfile in os.listdir(os.path.join(dest_dir, 'mysubdir')):
            assert dfile in dest_files


def print_outputs(response):
    print response.status_code
    print response.std_out
    print response.std_err



