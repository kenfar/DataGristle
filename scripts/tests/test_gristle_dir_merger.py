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
from pprint import pprint as pp

import test_tools

mod = test_tools.load_script('gristle_dir_merger')


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
    with file(fname, 'a'):
        os.utime(fname, times)




