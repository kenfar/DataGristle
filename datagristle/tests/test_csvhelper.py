#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2020 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import sys
import tempfile
import random
import csv
import os
from os.path import dirname

import pytest

import datagristle.csvhelper as csvhelper



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
                                                      escapechar=None)
        assert override_dialect.delimiter == '|'
        assert override_dialect.quoting == csv.QUOTE_NONE
        assert override_dialect.quotechar == '!'
        assert override_dialect.has_header is False
        assert override_dialect.doublequote is False
        assert override_dialect.escapechar == '\\'


class TestGetDialect(object):

    def test_get_overridden_dialect(self):

        fqfn = generate_test_file('|', csv.QUOTE_ALL, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn],
                                                  delimiter=',',
                                                  quoting='quote_none',
                                                  quotechar='!',
                                                  has_header=True,
                                                  doublequote=False,
                                                  escapechar='\\')

        assert resulting_dialect.delimiter == ','
        assert resulting_dialect.quoting == csv.QUOTE_NONE
        assert resulting_dialect.quotechar == '!'
        assert resulting_dialect.has_header is True
        assert resulting_dialect.doublequote is False
        assert resulting_dialect.escapechar == '\\'

    def test_get_dialect_from_file(self):

        fqfn = generate_test_file('|', csv.QUOTE_ALL, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn],
                                                  delimiter=None,
                                                  quoting=None,
                                                  quotechar=None,
                                                  has_header=None,
                                                  doublequote=None,
                                                  escapechar=None)
        assert resulting_dialect.delimiter == '|'
        assert resulting_dialect.quoting == csv.QUOTE_ALL
        assert resulting_dialect.quotechar == '"'
        assert resulting_dialect.has_header is False
        assert resulting_dialect.doublequote is False
        assert resulting_dialect.escapechar is None

    def test_empty_file(self):

        fqfn = generate_test_file('|', csv.QUOTE_ALL, 0)

        with pytest.raises(EOFError):
            resulting_dialect = csvhelper.get_dialect([fqfn],
                                                      delimiter=None,
                                                      quoting=None,
                                                      quotechar=None,
                                                      has_header=None,
                                                      doublequote=None,
                                                      escapechar=None)
    def test_multiple_files(self):

        fqfn1 = generate_test_file('|', csv.QUOTE_ALL, 0)
        fqfn2 = generate_test_file('|', csv.QUOTE_ALL, 1000)

        resulting_dialect = csvhelper.get_dialect([fqfn1, fqfn2],
                                                  delimiter=None,
                                                  quoting=None,
                                                  quotechar=None,
                                                  has_header=None,
                                                  doublequote=None,
                                                  escapechar=None)
        assert resulting_dialect.delimiter == '|'
        assert resulting_dialect.quoting == csv.QUOTE_ALL
        assert resulting_dialect.quotechar == '"'
        assert resulting_dialect.has_header is False



def generate_test_file(delim, quoting, record_cnt):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd, "w")
    name_list = ['smith', 'jones', 'thompson', 'ritchie']
    role_list = ['pm', 'programmer', 'dba', 'sysadmin', 'qa', 'manager']
    proj_list = ['cads53', 'jefta', 'norma', 'us-cepa']

    for i in range(record_cnt):
        name = random.choice(name_list)
        role = random.choice(role_list)
        proj = random.choice(proj_list)
        if quoting in (csv.QUOTE_MINIMAL, csv.QUOTE_ALL):
            name = '"' + name + '"'
            role = '"' + role + '"'
            proj = '"' + proj + '"'
        num = i
        if quoting == csv.QUOTE_ALL:
            num = '"' + str(i) + '"'
        record = f'''{num}{delim}{proj}{delim}{role}{delim}{name}\n'''
        #print(record)
        fp.write(record)

    fp.close()
    return fqfn
