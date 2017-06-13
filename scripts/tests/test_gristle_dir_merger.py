#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import time
import tempfile
import random
import csv
import pytest
import shutil
import envoy
from pprint import pprint as pp
from os.path import dirname, join as pjoin

pgm_path = dirname(dirname(os.path.realpath(__file__)))
root_path = dirname(pgm_path)

sys.path.insert(0, root_path)
import datagristle.test_tools as test_tools

mod = test_tools.load_script(pjoin(pgm_path, 'gristle_dir_merger'))



class TestCreateUniqueFileName(object):

    def setup_method(self, method):
        self.dir_name = tempfile.mkdtemp(prefix='test_gristle_dir_merger_')
    def teardown_method(self, method):
        shutil.rmtree(self.dir_name)

    def test_simple_file_name_with_extension(self):
        touch(os.path.join(self.dir_name, 'test.txt'))
        assert 'test.1.txt' == mod.create_unique_file_name(self.dir_name, 'test.txt') 

    def test_simple_file_name_without_extension(self):
        touch(os.path.join(self.dir_name, 'test'))
        assert 'test.1' == mod.create_unique_file_name(self.dir_name, 'test') 

    def test_simple_file_name_without_prior_file(self):
        assert 'test.txt' == mod.create_unique_file_name(self.dir_name, 'test.txt') 

    def test_simple_file_name_with_multiple_dups(self):
        touch(os.path.join(self.dir_name, 'test.txt'))
        touch(os.path.join(self.dir_name, 'test.1.txt'))
        touch(os.path.join(self.dir_name, 'test.2.txt'))
        assert 'test.3.txt' == mod.create_unique_file_name(self.dir_name, 'test.txt') 

    def test_simple_file_name_with_multiple_extensions(self):
        touch(os.path.join(self.dir_name, 'test.boo.txt'))
        assert 'test.boo.1.txt' == mod.create_unique_file_name(self.dir_name, 'test.boo.txt') 

    def test_simple_file_name_with_multiple_empty_extensions(self):
        touch(os.path.join(self.dir_name, 'test..txt'))
        assert 'test..1.txt' == mod.create_unique_file_name(self.dir_name, 'test..txt') 

        touch(os.path.join(self.dir_name, 'test..'))
        assert 'test..1.' == mod.create_unique_file_name(self.dir_name, 'test..') 








def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def generate_file(temp_dir, records=1):
    (fd, fqfn) = tempfile.mkstemp(prefix='test_md5_', dir=temp_dir)

    fp = os.fdopen(fd,"w")
    for x in range(records):
        fp.write('blahblahblahfidoblahblah\n')
    fp.close()

    cmd = 'md5sum %s' % fqfn
    r   = envoy.run(cmd)
    assert r.status_code == 0, 'generate_file md5sum failed'
    md5sum, fn  = r.std_out.split()

    return fqfn, md5sum





