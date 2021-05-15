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

import datagristle.csvhelper as csvhelper
import datagristle.test_tools as ttools



class TestOverrideDialect(object):

    def test_override(self):
        dialect = csvhelper.Dialect(delimiter='|',
                                    has_header=False,
                                    quoting=csv.QUOTE_NONE,
                                    quotechar=None,
                                    doublequote=None,
                                    escapechar=None)
        override_dialect = csvhelper.override_dialect(dialect,
                                                      delimiter=',',
                                                      quoting='QUOTE_ALL',
                                                      quotechar='"',
                                                      has_header=False,
                                                      doublequote=False,
                                                      skipinitialspace=False,
                                                      escapechar='\\')
        assert override_dialect.delimiter == ','
        assert override_dialect.quoting == csv.QUOTE_ALL
        assert override_dialect.quotechar == '"'
        assert override_dialect.has_header is False
        assert override_dialect.doublequote is False
        assert override_dialect.escapechar == '\\'

    def test_non_override(self):
        dialect = csvhelper.Dialect(delimiter='|',
                                    has_header=False,
                                    quoting=csv.QUOTE_NONE,
                                    quotechar='!',
                                    doublequote=False,
                                    escapechar='\\')
        override_dialect = csvhelper.override_dialect(dialect,
                                                      delimiter=None,
                                                      quoting=None,
                                                      quotechar=None,
                                                      has_header=None,
                                                      doublequote=None,
                                                      skipinitialspace=False,
                                                      escapechar=None)
        assert override_dialect.delimiter == '|'
        assert override_dialect.quoting == csv.QUOTE_NONE
        assert override_dialect.quotechar == '!'
        assert override_dialect.has_header is False
        assert override_dialect.doublequote is False
        assert override_dialect.escapechar == '\\'


class TestGetDialect(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_get_overridden_dialect(self):

        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        fqfn = ttools.make_team_file(self.temp_dir, dialect, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn],
                                                  delimiter=',',
                                                  quoting='quote_none',
                                                  quotechar='!',
                                                  has_header=True,
                                                  doublequote=False,
                                                  escapechar='\\',
                                                  skipinitialspace=False,
                                                  verbosity='normal')

        assert resulting_dialect.delimiter == ','
        assert resulting_dialect.quoting == csv.QUOTE_NONE
        assert resulting_dialect.quotechar == '!'
        assert resulting_dialect.has_header is True
        assert resulting_dialect.doublequote is False
        assert resulting_dialect.escapechar == '\\'

    def test_get_dialect_from_file(self):

        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        fqfn = ttools.make_team_file(self.temp_dir, dialect, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn],
                                                  delimiter=None,
                                                  quoting=None,
                                                  quotechar=None,
                                                  has_header=None,
                                                  doublequote=None,
                                                  escapechar=None,
                                                  skipinitialspace=False,
                                                  verbosity='normal')
        assert resulting_dialect.delimiter == '|'
        assert resulting_dialect.quoting == csv.QUOTE_ALL
        assert resulting_dialect.quotechar == '"'
        assert resulting_dialect.has_header is False
        assert resulting_dialect.doublequote is False
        assert resulting_dialect.escapechar is None

    def test_empty_file(self):

        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        fqfn = ttools.make_team_file(self.temp_dir, dialect, 0)

        with pytest.raises(EOFError):
            resulting_dialect = csvhelper.get_dialect([fqfn],
                                                      delimiter=None,
                                                      quoting=None,
                                                      quotechar=None,
                                                      has_header=None,
                                                      doublequote=None,
                                                      escapechar=None,
                                                      skipinitialspace=False,
                                                      verbosity='normal')
    def test_multiple_files(self):

        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=False)
        fqfn1 = ttools.make_team_file(self.temp_dir, dialect, 0)
        fqfn2 = ttools.make_team_file(self.temp_dir, dialect, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn1, fqfn2],
                                                  delimiter=None,
                                                  quoting=None,
                                                  quotechar=None,
                                                  has_header=None,
                                                  doublequote=None,
                                                  escapechar=None,
                                                  skipinitialspace=False,
                                                  verbosity='normal')
        assert resulting_dialect.delimiter == '|'
        assert resulting_dialect.quoting == csv.QUOTE_ALL
        assert resulting_dialect.quotechar == '"'
        assert resulting_dialect.has_header is False



class TestHeader(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    def test_load_and_gets(self):
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=True)
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
        dialect = csvhelper.Dialect(delimiter='|', quoting=csv.QUOTE_ALL, has_header=True)
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

