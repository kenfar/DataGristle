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


class TestMergeEmpties(object):
    """ Tests gristle_dir_merger when used with empty directoreis.
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

    def test_empty_to_empty(self):

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.dest_dir,
                          'dest_dir':   self.source_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0

    def test_nonempty_to_empty(self):

        tt.touch(os.path.join(self.source_dir, 'foo.csv'))

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'foo.csv' in os.listdir(self.dest_dir)
        assert 'foo.csv' not in os.listdir(self.source_dir)


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
                         -c name                   \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))




class TestMergeByNameOnly(object):
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
            \tmp\TestGristleDirMerger_dest_???\mysubdir\foo.csv
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
                         -c name                   \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'bar.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)



class TestMergeByNameAndSize(object):
    """ Tests gristle_dir_merger with criteria of name only.
    """

    def setup_method(self, method):
        self.source_dir = tempfile.mkdtemp(prefix='TestGristleDirMerger_source_')
        self.dest_dir   = tempfile.mkdtemp(prefix='TestGristleDirMerger_dest_')

    def teardown_method(self, method):
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.dest_dir)

    def get_outputs(self, response):
        print ' '.join(response.command)
        print response.status_code
        print response.std_out
        print response.std_err

    def test_basics_unique_names_in_identical_subdirs(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir' deleted
            \tmp\*_source_?\mysubdir\foo.csv  # file moved
            \tmp\*_dest_???\mysubdir\bar.csv
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir\bar.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        tt.touch(os.path.join(source_subdir, 'foo.csv'))

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        tt.touch(os.path.join(dest_subdir, 'bar.csv'))

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name size              \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'bar.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)

    def test_basics_unique_names_in_a_new_subdir(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir' moved
            \tmp\*_source_?\mysubdir\foo.csv  # file moved
            \tmp\*_dest_???
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir\foo.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        tt.touch(os.path.join(source_subdir, 'foo.csv'))

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name size              \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)


    def test_files_with_same_sizes(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir                # 'mysubdir' deleted
            \tmp\*_source_?\mysubdir\foo.csv 0 len  # file moved
            \tmp\*_dest_???\mysubdir\foo.csv 0 len
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir\foo.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        tt.touch(os.path.join(source_subdir, 'foo.csv'))

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        tt.touch(os.path.join(dest_subdir, 'foo.csv'))

        self.cmd = """%(pgm)s %(source_dir)s %(dest_dir)s         \
                         -c name size        -a first_wins        \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)

    def test_files_with_diff_sizes(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir                # 'mysubdir' deleted
            \tmp\*_source_?\mysubdir\foo.csv 0 len  # file moved
            \tmp\*_dest_???\mysubdir\foo.csv 5 len
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir\foo.csv
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        create_test_file(source_subdir, 'foo.csv', 'blahblahblah') # same name, bigger

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', '')     #same name but smaller

        self.cmd = """%(pgm)s %(source_dir)s %(dest_dir)s         \
                         -c name size        -a first_wins        \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'foo.1.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))


class TestActionFirstWins(object):
    """ Tests gristle_dir_merger with action of first_wins.
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

    def test_first_in_dest_dir(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir' deleted
            \tmp\*_source_?\mysubdir\foo.csv, contents='last'  # file deleted
            \tmp\*_dest_???\mysubdir          # 'mysubdir' kept
            \tmp\*_dest_???\mysubdir\foo.csv, contents='first' # file kept
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv, contents='first'
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        create_test_file(source_subdir, 'foo.csv', 'last-file')

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', 'first-file')

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a first_wins             \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 'first-file' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))


class TestActionLastWins(object):
    """ Tests gristle_dir_merger with action of last_wins.
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

    def test_last_in_dest_dir(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir' deleted
            \tmp\*_source_?\mysubdir\foo.csv, contents='last'  # moved
            \tmp\*_dest_???\mysubdir          # 'mysubdir' kept
            \tmp\*_dest_???\mysubdir\foo.csv, contents='first' # overridden
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv, contents='last'
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        create_test_file(source_subdir, 'foo.csv', 'last-file')

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', 'first-file')

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a last_wins              \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 'last-file' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))


class TestActionBiggestWins(object):
    """ Tests gristle_dir_merger with action of biggest_wins.
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

    def test_biggest_in_dest_dir(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir'    # deleted
            \tmp\*_source_?\mysubdir\foo.csv, contents='blahblahblah' # moved
            \tmp\*_source_?\mysubdir\bar.csv, contents=''     # deleted
            \tmp\*_dest_???\mysubdir          # 'mysubdir'    # kept
            \tmp\*_dest_???\mysubdir\foo.csv, contents=''     # overridden
            \tmp\*_dest_???\mysubdir\bar.csv, contents='blahblahblah' # kept
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv, contents='blah'
            \tmp\*_dest_???\mysubdir\bar.csv, contents='blah'
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)
        create_test_file(source_subdir, 'foo.csv', 'blahblahblah')
        create_test_file(source_subdir, 'bar.csv', '')

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', '')
        create_test_file(dest_subdir, 'bar.csv', 'blahblahblah')

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a biggest_wins           \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 'blahblahblah' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))
        assert 'blahblahblah' == get_file_contents(os.path.join(self.dest_dir, 'mysubdir', 'bar.csv'))



class TestActionMostCurrentWins(object):
    """ Tests gristle_dir_merger with action of most_current_wins.
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

    def test_most_curr_in_dest_dir(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir'    # deleted
            \tmp\*_source_?\mysubdir\foo.csv, date of 2014    # moved
            \tmp\*_source_?\mysubdir\bar.csv, date of 1999    # deleted
            \tmp\*_dest_???\mysubdir          # 'mysubdir'    # kept
            \tmp\*_dest_???\mysubdir\foo.csv, date of 1999    # overridden
            \tmp\*_dest_???\mysubdir\bar.csv, date of 2014    # kept
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv, date of 2014
            \tmp\*_dest_???\mysubdir\bar.csv, date of 2014
        """
        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)

        create_test_file(source_subdir, 'foo.csv', '', 2014)
        create_test_file(source_subdir, 'bar.csv', '', 1999)

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', '', 1999)
        create_test_file(dest_subdir, 'bar.csv', '', 2014)

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a most_current_wins      \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir' in os.listdir(self.dest_dir)
        assert 'foo.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir' not in os.listdir(self.source_dir)
        assert 2014 == get_file_myear(os.path.join(self.dest_dir, 'mysubdir', 'foo.csv'))
        assert 2014 == get_file_myear(os.path.join(self.dest_dir, 'mysubdir', 'bar.csv'))


class TestActionAllWins(object):
    """ Tests gristle_dir_merger with action of most_current_wins.
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

    def test_basics(self):
        """      starting dirs & files:
            \tmp\*_source_?\mysubdir          # 'mysubdir'    # deleted
            \tmp\*_source_?\mysubdir\foo.csv  # moved
            \tmp\*_dest_???\mysubdir          # 'mysubdir'    # kept
            \tmp\*_dest_???\mysubdir\foo.csv  # kept
                  should become:
            \tmp\*_source_?
            \tmp\*_dest_???\mysubdir
            \tmp\*_dest_???\mysubdir\foo.csv
            \tmp\*_dest_???\mysubdir\foo.1.csv
        """

        source_subdir = os.path.join(self.source_dir, 'mysubdir')
        os.mkdir(source_subdir)

        create_test_file(source_subdir, 'foo.csv', '')

        dest_subdir = os.path.join(self.dest_dir, 'mysubdir')
        os.mkdir(dest_subdir)
        create_test_file(dest_subdir, 'foo.csv', '')

        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a all_wins               \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir'   in os.listdir(self.dest_dir)
        assert 'foo.csv'    in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'foo.1.csv'  in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'mysubdir'   not in os.listdir(self.source_dir)


class TestDeepDirectory(object):
    """ Tests gristle_dir_merger with action of most_current_wins.
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


        self.cmd = """%(pgm)s %(source_dir)s       \
                              %(dest_dir)s         \
                         -c name                   \
                         -a first_wins             \
                         --log-level debug         \
                   """ % {'pgm': PGM,
                          'source_dir': self.source_dir,
                          'dest_dir':   self.dest_dir}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)

        assert r.status_code      == 0
        assert 'mysubdir'   not in os.listdir(self.source_dir)
        assert 'mysubdir'   in os.listdir(self.dest_dir)
        assert 'foo'        in os.listdir(os.path.join(self.dest_dir, 'mysubdir'))
        assert 'foo.csv'    in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo'))
        assert 'foo2'       in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo'))
        assert 'foo2.csv'   in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2'))
        assert 'foo3'       in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2'))
        assert 'foo3.csv'   in os.listdir(os.path.join(self.dest_dir, 'mysubdir', 'foo', 'foo2', 'foo3'))



def create_test_file(path, file_name, contents, year=None):
    with open(os.path.join(path, file_name), 'w') as f:
        f.write(contents)
    if year:
        t = time.mktime(time.strptime('01.01.%d 00:00:00' % year, '%d.%m.%Y %H:%M:%S'))
        os.utime(os.path.join(path, file_name), (t, t))


def get_file_contents(fqfn):
    with open(fqfn, 'r') as f:
        return f.read()


def get_file_myear(fqfn):
    filemtime = os.path.getmtime(fqfn)
    return int(time.strftime('%Y', time.localtime(filemtime)))
