#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

import tempfile
import shutil
import os
from os.path import dirname, join as pjoin

import envoy

import datagristle.test_tools as test_tools

pgm_path = dirname(dirname(os.path.realpath(__file__)))
mod = test_tools.load_script(pjoin(pgm_path, 'gristle_dir_merger'))



class TestCreateUniqueFileName(object):

    def setup_method(self, method):
        self.dir_name = tempfile.mkdtemp(prefix='test_gristle_dir_merger_')

    def teardown_method(self, method):
        shutil.rmtree(self.dir_name)

    def test_simple_file_name_with_extension(self):
        touch(os.path.join(self.dir_name, 'test.txt'))
        assert mod.create_unique_file_name(self.dir_name, 'test.txt') == 'test.1.txt'

    def test_simple_file_name_without_extension(self):
        touch(os.path.join(self.dir_name, 'test'))
        assert mod.create_unique_file_name(self.dir_name, 'test') == 'test.1'

    def test_simple_file_name_without_prior_file(self):
        assert mod.create_unique_file_name(self.dir_name, 'test.txt') == 'test.txt'

    def test_simple_file_name_with_multiple_dups(self):
        touch(os.path.join(self.dir_name, 'test.txt'))
        touch(os.path.join(self.dir_name, 'test.1.txt'))
        touch(os.path.join(self.dir_name, 'test.2.txt'))
        assert mod.create_unique_file_name(self.dir_name, 'test.txt') == 'test.3.txt'

    def test_simple_file_name_with_multiple_extensions(self):
        touch(os.path.join(self.dir_name, 'test.boo.txt'))
        assert mod.create_unique_file_name(self.dir_name, 'test.boo.txt') == 'test.boo.1.txt'

    def test_simple_file_name_with_multiple_empty_extensions(self):
        touch(os.path.join(self.dir_name, 'test..txt'))
        assert mod.create_unique_file_name(self.dir_name, 'test..txt') == 'test..1.txt'

        touch(os.path.join(self.dir_name, 'test..'))
        assert mod.create_unique_file_name(self.dir_name, 'test..') == 'test..1.'



def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def generate_file(temp_dir, records=1):
    (filedesc, fqfn) = tempfile.mkstemp(prefix='test_md5_', dir=temp_dir)

    fileobj = os.fdopen(filedesc, "w")
    for _ in range(records):
        fileobj.write('blahblahblahfidoblahblah\n')
    fileobj.close()

    cmd = 'md5sum %s' % fqfn
    runner = envoy.run(cmd)
    assert runner.status_code == 0, 'generate_file md5sum failed'
    md5sum, _ = runner.std_out.split()

    return fqfn, md5sum





