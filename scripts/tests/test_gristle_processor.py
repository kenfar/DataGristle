#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import time
import datetime
import tempfile
import random
import csv
import pytest
import shutil
from pprint import pprint as pp
from os.path import dirname, join as pjoin

pgm_path = dirname(dirname(os.path.realpath(__file__)))
root_path = dirname(pgm_path)

sys.path.insert(0, root_path)
import datagristle.test_tools as test_tools

mod = test_tools.load_script(pjoin(pgm_path, 'gristle_processor'))


class Test_ProcessDir(object):

    def setup_method(self, method):
        self.tmpdir    = tempfile.mkdtemp(prefix="gristle_processor_")
        for i in range(20):
            suffix = '_2013-03-10_'
            create_file(self, age=None, suffix=suffix, mydir=self.tmpdir)

        self.kwargs = {  'name': 'foobar',
                         'gathering_phase': {'dir': '%s' % self.tmpdir},
                         'inclusion_phase': {
                                             #'atime_gt': '100d',
                                             #'atime_lt': '90d',
                                             #'custom': None,
                                             #'file_ownership': 'list',
                                             #'file_privs': 'list',
                                             #'file_size': 'range',
                                             'file_type': 'file',
                                             'fntime_filter_regex':  '_20[1-3]\d-[0-1]\d-[0-3]\d_',
                                             'fntime_extract_regex': '20[1-3]\d-[0-1]\d-[0-3]\d',
                                             'fntime_format': '%Y-%m-%d',
                                             'fntime_op': 'lt',
                                             'fntime_time': 'current_time - 100 days'},
                                             #'mmin': 50,
                                             #'mtime': 50,
                                             #'mtime_eq': None},
                         #'exclusion_phase': {'atime_gt': None,
                         #                    'file_privs': None,
                         #                    'file_size': None,
                         #                    'file_type': None},
                         'action_phase': {'action_builtin': 'list' },
                    }

    def teardown_method(self, method):
        shutil.rmtree(self.tmpdir)

    def test_bad_dir(self):
        """ProcessDir must raise an exception if the directory doesn't exist.
           Testing against a random directory name.
        """
        self.kwargs['gathering_phase']['dir'] = '/lkj4j<F5>nmjfdskfd094kdnja'
        with pytest.raises(SystemExit):
            pd = mod.ProcessDir(self.kwargs)

    def test_inclusion_phase(self):
        """Just checks to see if it can make it thru this phase.
        """
        #del self.kwargs['inclusion_phase']['mmin']
        #del self.kwargs['inclusion_phase']['mtime']
        #del self.kwargs['inclusion_phase']['mtime_eq']
        #del self.kwargs['inclusion_phase']['atime_gt']
        #del self.kwargs['inclusion_phase']['atime_lt']
        del self.kwargs['inclusion_phase']['file_type']
        #del self.kwargs['inclusion_phase']['file_size']
        #del self.kwargs['inclusion_phase']['file_privs']
        #del self.kwargs['inclusion_phase']['file_ownership']
        #del self.kwargs['inclusion_phase']['custom']
        mod.setup_logs(arg_log_dir=None)
        pd = mod.ProcessDir(self.kwargs)
        pd.walk()






class Test_FileAnalyzer_misc(object):

    def setup_method(self, method):
        pass

    def test_is_numeric(self):
        assert mod.isnumeric(3)      is True
        assert mod.isnumeric(3.3)    is True
        assert mod.isnumeric(-3.3)   is True
        assert mod.isnumeric('5')    is True
        assert mod.isnumeric('-3')   is True
        assert mod.isnumeric('0')    is True
        assert mod.isnumeric('5.5')  is True
        assert mod.isnumeric('5.5b') is False
        assert mod.isnumeric('c')    is False
        assert mod.isnumeric(None)   is False

    def test_get_delta(self):
        #file_analyzer = mod.FileAnalyzer('foo.txt', {}, {})
        file_analyzer = mod.FileAnalyzer({}, {})
        assert file_analyzer._get_delta('3s')    == 3
        assert file_analyzer._get_delta('3s')    == 3
        assert file_analyzer._get_delta('0s')    == 0
        assert file_analyzer._get_delta('1m')    == 60
        assert file_analyzer._get_delta('2m')    == 120
        assert file_analyzer._get_delta('1h')    == 3600
        assert file_analyzer._get_delta('2h')    == 7200
        assert file_analyzer._get_delta('1d')    == 86400
        assert file_analyzer._get_delta('100d')  == 86400 * 100
        assert file_analyzer._get_delta('1000d') == 86400 * 1000
        assert file_analyzer._get_delta('1w')    == 86400 * 7
        assert file_analyzer._get_delta('1M')    == 86400 * 30
        assert file_analyzer._get_delta('1y')    == 86400 * 365

        assert file_analyzer._get_delta('current_time - 1 day') \
                == 86400 
        assert file_analyzer._get_delta('current_time - 10 day') \
                == 86400 * 10
        assert file_analyzer._get_delta('current_time - 2 weeks') \
                == 86400 * 14
        assert file_analyzer._get_delta('current_time - 1 month') \
                == 86400 * 30

        with pytest.raises(ValueError):
            assert file_analyzer._get_delta('3') == 3

        with pytest.raises(ValueError):
            assert file_analyzer._get_delta('3') == 3



class Test_FileAnalyzer_check_times(object):

    def setup_method(self, method):
        self.tmpdir    = tempfile.mkdtemp(prefix="gristle_processor_")

    def teardown_method(self, method):
        shutil.rmtree(self.tmpdir)


    def test_mtime_op_argdate_10s_vs_100sfile(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_', dir=self.tmpdir)
        curr_time  = time.time()
        touch(fqfn, (curr_time-100, curr_time-100))
        file_analyzer = mod.FileAnalyzer({}, {})
        print('--- 0s ---')
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '0s')
        print('--- 10s ---')
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '10s')

    def test_mtime_op_argdate_200s_vs_100sfile(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_', dir=self.tmpdir)
        curr_time  = time.time()
        touch(fqfn, (curr_time-100, curr_time-100))
        file_analyzer = mod.FileAnalyzer({}, {})
        print('--- 200s ---')
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '200s') is False

    def test_mtime_op_argdate_10dfile(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_', dir=self.tmpdir)
        curr_time  = time.time()
        touch(fqfn, (curr_time-(86400*10), curr_time-(86400*10)))
        file_analyzer = mod.FileAnalyzer({}, {})

        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '200h')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '600h')  is False
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '11d')  is False
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '10d')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '9d')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '1w')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '2w')  is False
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '0M')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '1M')  is False
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '2M')  is False
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '0y')  is True
        assert file_analyzer._mtime_op_argdate(fqfn, 'lt', '1y')  is False

    def test_atime_op_argdate_10dfile(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_', dir=self.tmpdir)
        curr_time  = time.time()
        touch(fqfn, (curr_time-(86400*10), curr_time-(86400*10)))
        file_analyzer = mod.FileAnalyzer({}, {})

        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '200h')  is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '600h')  is False
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '11d')   is False
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '10d')   is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '9d')    is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '5d')    is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '1w')    is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '2w')    is False
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '0M')    is True
        assert file_analyzer._atime_op_argdate(fqfn, 'lt', '1M')    is False



class TestFileAnalyzerFileNameDate(object):

    def setup_method(self, method):
        self.tmpdir    = tempfile.mkdtemp(prefix="gristle_processor_")

    def teardown_method(self, method):
        shutil.rmtree(self.tmpdir)

    def make_file_date(self, days):
        mytime = time.localtime(time.time() - 86400 * days)
        return time.strftime('%Y-%m-%d', mytime)

    def create_file(self, age, suffix='_foo'):
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_', suffix=suffix, dir=self.tmpdir)
        file_time  = time.time() - age
        touch(fqfn, (file_time, file_time))
        return fqfn

    def create_file_with_specific_name(self, age, fqfn):
        file_time  = time.time() - age
        touch(fqfn, (file_time, file_time))


    def test_file_with_no_date_through_filter_regex(self):
        fdate   = self.make_file_date(100)  # looks like '2014-03-14'
        fqfn    = self.create_file(age=86400*10, suffix='foo_%s_bear' % fdate)
        fa      = mod.FileAnalyzer({}, {})
        ext_regex     = fdate               # looks like '2014-03-14'
        filter_regex  = '_%s_' % ext_regex  # looks like '_2014-03-14_'
        assert fa._filenamedate_op_argdate('foo.csv', filter_regex, ext_regex,
                                    '%Y-%m-%d', 'lt', '10d') is None

    def test_failed_extract_regex(self):
        """ The extract regex must be able to find the date within the filter
            regex.  If not, it's a user-error in defining these regexes.
        """
        fdate   = self.make_file_date(100)  # looks like '2014-03-14'
        fqfn    = self.create_file(age=86400*10, suffix='foo_%s_bear' % fdate)
        fa      = mod.FileAnalyzer({}, {})
        ext_regex     = 'food'              # won't match date
        filter_regex  = '_%s_' % fdate      # looks like '_2014-03-14_'
        with pytest.raises(ValueError):
            fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                    '%Y-%m-%d', 'lt', '10d') is None

    def test_bad_format(self):
        fdate   = self.make_file_date(100)  # looks like '2014-03-14'
        fqfn    = self.create_file(age=86400*10, suffix='foo_%s_bear' % fdate)
        fa      = mod.FileAnalyzer({}, {})
        ext_regex     = fdate               # looks like '2014-03-14'
        filter_regex  = '_%s_' % ext_regex  # looks like '_2014-03-14_'
        fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                    '%9', 'lt', '10d') is None

    def test_bad_op(self):
        fdate   = self.make_file_date(100)  # looks like '2014-03-14'
        fqfn    = self.create_file(age=86400*10, suffix='foo_%s_bear' % fdate)
        fa      = mod.FileAnalyzer({}, {})
        ext_regex     = fdate               # looks like '2014-03-14'
        filter_regex  = '_%s_' % ext_regex  # looks like '_2014-03-14_'
        with pytest.raises(AssertionError):
           fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                        '%Y-%m-%d', 'gg', '10d') is None

    def test_filenamedate_op_argdate(self):
        fdate         = self.make_file_date(100) # looks like '2014-03-14'
        fqfn          = self.create_file(age=86400*10, suffix='foo_%s_bear' % fdate)
        fa = mod.FileAnalyzer({}, {})
        ext_regex     = fdate               # looks like '2014-03-14'
        filter_regex  = '_%s_' % ext_regex  # looks like '_2014-03-14_'

        assert fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                    '%Y-%m-%d', 'lt', '10d') is True
        assert fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                    '%Y-%m-%d', 'lt', '100d') is True
        assert fa._filenamedate_op_argdate(fqfn, filter_regex, ext_regex,
                                    '%Y-%m-%d', 'gt', '1000d') is True

    def test_filenamedate_op_argdate_nothing_but_date(self):
        fa = mod.FileAnalyzer({}, {})
        ext_regex     = '^201[3-9][0-1][0-9][0-3][0-9]$'
        # create a date in format: YYYYMMDD
        file_name     = (datetime.datetime.utcnow() - datetime.timedelta(days=200)).date().isoformat().replace('-', '')
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is True
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'gt', '1000d') is True
        file_name     = 'a20140101b'
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is None

    def test_filenamedate_op_argdate_simplest_date(self):
        fa = mod.FileAnalyzer({}, {})
        ext_regex     = '201[3-9][0-1][0-9][0-3][0-9]'
        # create a date in format: YYYYMMDD
        file_name     = (datetime.datetime.utcnow() - datetime.timedelta(days=200)).date().isoformat().replace('-', '')
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is True
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'gt', '1000d') is True
        file_name     = 'a20140101b'
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is True

    def test_filenamedate_op_argdate_anchored_simple_date(self):
        fa = mod.FileAnalyzer({}, {})
        ext_regex     = '^201[3-9][0-1][0-9][0-3][0-9]$'
        # create a date in format: YYYYMMDD
        file_name     = (datetime.datetime.utcnow() - datetime.timedelta(days=200)).date().isoformat().replace('-', '')
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is True
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'gt', '1000d') is True

        file_name     = '_20140101_' # without filter regex so should fail
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is None
        assert fa._filenamedate_op_argdate(file_name, None, ext_regex,
                                    '%Y%m%d', 'gt', '1000d') is None

    def test_filenamedate_op_argdate_with_simple_date_and_surrounding_chars(self):
        fa            = mod.FileAnalyzer({}, {})
        yyyymmdd      = (datetime.datetime.utcnow() - datetime.timedelta(days=200)).date().isoformat().replace('-', '')
        file_name     = '_date-{}_'.format(yyyymmdd)
        filter_regex  = '_date-201[3-9][0-1][0-9][0-3][0-9]_'
        ext_regex     = '201[3-9][0-1][0-9][0-3][0-9]'
        assert fa._filenamedate_op_argdate(file_name, filter_regex, ext_regex,
                                    '%Y%m%d', 'lt', '10d') is True
        assert fa._filenamedate_op_argdate(file_name, filter_regex, ext_regex,
                                    '%Y%m%d', 'gt', '1000d') is True






class Test_get_regex_substring(object):

    def setup_method(self, method):
        pass

    def test_extract_only(self):

        fqfn          = 'ProcessorTestIn_blahfoobarf_2014-03-14_baz'
        extract_regex = '20[1-3]\d-[0-1]\d-[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex) == '2014-03-14'

        fqfn          = 'ProcessorTestIn_blahfoobarf_20140314_baz'
        extract_regex = '20[1-3]\d[0-1]\d[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex) == '20140314'

        fqfn          = 'ProcessorTestIn_blahfoobarf_2014-03-14.19.22.01_baz'
        extract_regex = '20[1-3]\d-[0-1]\d-[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex) == '2014-03-14'

        fqfn          = 'ProcessorTestIn_blahfoobarf_baz.gz'
        extract_regex = '20[1-3]\d-[0-1]\d-[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex) is None

        fqfn          = 'ProcessorTestIn_blahfoobarf_baz.gz'
        extract_regex = '20[1-3]\d-[0-1]\d-[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex) is None

        fqfn          = '20140101'
        extract_regex = '201[3-9][0-1][0-9][0-3][0-9]'
        assert mod.get_regex_substring(fqfn, extract_regex) == '20140101'

        fqfn          = '20140101'
        extract_regex = '^201[3-9][0-1][0-9][0-3][0-9]$'
        assert mod.get_regex_substring(fqfn, extract_regex) == '20140101'


    def test_filter_and_extract_mismatch_on_filter(self):
        fqfn          = 'ProcessorTestIn_blahfoobarf_baz.gz'
        filter_regex  = '_20[1-3]\d-[0-1]\d-[0-3]\d_'
        extract_regex = '20[1-3]\d-[0-1]\d-[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex, filter_regex) is None

    def test_filter_and_extract_mismatch_on_extract(self):
        """ First run the filter_regex to find the date surrounded by
            underscores.  Then run the extract_regex to pull out just the
            date within the underscores.

            In this case the filter_regex will be successful, but the extract
            won't.  Normally, this shouldn't happen, but easily can if the user
            has a mistake in their two regexes.
        """
        fqfn          = 'ProcessorTestIn__2014-03-04_blahfoobarf_baz.gz'
        filter_regex  = '_20[1-3]\d-[0-1]\d-[0-3]\d_'
        extract_regex = '2099-[0-1]\d-[0-3]\d'
        with pytest.raises(ValueError):
           mod.get_regex_substring(fqfn, extract_regex, filter_regex) 

    def test_filter_and_extract_success(self):
        fqfn          = 'ProcessorTestIn_foo20931415barf_20140314_baz.gz'
        filter_regex  = '_20[1-3]\d[0-1]\d[0-3]\d_'
        extract_regex = '20[1-3]\d[0-1]\d[0-3]\d'
        assert mod.get_regex_substring(fqfn, extract_regex, filter_regex) == '20140314'

        fqfn          = '_date-20140101_'
        filter_regex  = '_date-201[3-9][0-1][0-9][0-3][0-9]_'
        extract_regex = '201[3-9][0-1][0-9][0-3][0-9]'
        assert mod.get_regex_substring(fqfn, extract_regex, filter_regex) == '20140101'






def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def make_file_date(self, days):
    mytime = time.localtime(time.time() - 86400 * days)
    return time.strftime('%Y-%m-%d', mytime)


def create_file(self, age=None, suffix='foo', mydir=None):
    if mydir:
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_',
                                    suffix='_%s.csv' % suffix,
                                    dir=mydir)
    else:
        (fd, fqfn) = tempfile.mkstemp(prefix='ProcessorTestIn_',
                                    suffix='_%s.csv' % suffix)
    if age:
        file_time  = time.time() - age
        touch(fqfn, (file_time, file_time))

    return fqfn

