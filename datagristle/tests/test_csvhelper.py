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

import csv
import os
from os.path import dirname
from pprint import pprint as pp
import random
import shutil
import sys
import tempfile

import pytest

from datagristle import csvhelper
from datagristle import test_tools as ttools



class TestHeader(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_load_and_gets(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=True,
                                    quotechar='"', doublequote=False, escapechar=None,
                                    skipinitialspace=False)
        fqfn = ttools.make_team_file(self.temp_dir, dialect, 10)

        header = csvhelper.Header()
        header.load_from_file(fqfn, dialect)

        assert len(header.raw_field_names)
        assert len(header.field_names)

        assert header.get_field_position('role') == 2
        assert header.get_field_name(3) == 'name'

        assert header.get_field_position_from_any('3') == 3
        assert header.get_field_position_from_any('name') == 3


    def test_load_from_files(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=True,
                                    quotechar='"', doublequote=False, escapechar=None,
                                    skipinitialspace=False)
        fqfn1 = ttools.make_team_file(self.temp_dir, dialect, 0)
        fqfn2 = ttools.make_team_file(self.temp_dir, dialect, 10)

        header = csvhelper.Header()
        header.load_from_files([fqfn1, fqfn2], dialect)

        assert len(header.raw_field_names)
        assert len(header.field_names)

        assert header.get_field_position('role') == 2
        assert header.get_field_name(3) == 'name'

        assert header.get_field_position_from_any('3') == 3
        assert header.get_field_position_from_any('name') == 3



class TestBuildDialect(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.dialect_builder = csvhelper.BuildDialect()
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False,
                                    quotechar='"', doublequote=False, escapechar=None,
                                    skipinitialspace=False)
        self.fqfn = ttools.make_team_file(self.temp_dir, dialect, 1000)


    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_step1_discover(self):
        self.dialect_builder.step1_discover_dialect([self.fqfn])

        assert self.dialect_builder._step1.get('delimiter') == '|'
        assert csvhelper.get_quote_name(self.dialect_builder._step1.get('quoting')) \
               == 'QUOTE_ALL'
        assert self.dialect_builder._step1.get('has_header') == False


    def test_step2_override(self):
        self.dialect_builder.step1_discover_dialect([self.fqfn])
        self.dialect_builder.step2_override_dialect(delimiter='!',
                                                    has_header=True)

        assert self.dialect_builder._step2.get('delimiter') == '!'
        assert csvhelper.get_quote_name(self.dialect_builder._step2.get('quoting')) \
               == 'QUOTE_ALL'
        assert self.dialect_builder._step2.get('has_header') == True


    def test_step3_default(self):
        self.dialect_builder.step1_discover_dialect([self.fqfn])
        self.dialect_builder.step2_override_dialect(delimiter='!',
                                                    has_header=True)
        self.dialect_builder._step2['has_header'] = None
        self.dialect_builder.step3_default_dialect()

        assert self.dialect_builder._step3.get('delimiter') == '!'
        assert csvhelper.get_quote_name(self.dialect_builder._step3.get('quoting')) \
               == 'QUOTE_ALL'
        assert self.dialect_builder._step3.get('has_header') == False


    def test_step4_finalize(self):
        self.dialect_builder.step1_discover_dialect([self.fqfn])
        self.dialect_builder.step2_override_dialect(delimiter='!',
                                                    has_header=True)
        self.dialect_builder._step2['has_header'] = None
        self.dialect_builder.step3_default_dialect()
        self.dialect_builder.step4_finalize_dialect()

        assert self.dialect_builder.final != {}
        assert self.dialect_builder.dialect is not None


    def test_final_dialect(self):
        self.dialect_builder.step1_discover_dialect([self.fqfn])
        self.dialect_builder.step2_override_dialect(delimiter='!',
                                                    has_header=True)
        self.dialect_builder._step2['has_header'] = None
        self.dialect_builder.step3_default_dialect()
        self.dialect_builder.step4_finalize_dialect()
        dialect = self.dialect_builder.dialect

        assert dialect.delimiter == '!'
        assert dialect.quoting == 1



