#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2020 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import csv
import fileinput
from pprint import pprint as pp
import shutil
import tempfile
from os.path import dirname, basename
from os.path import join as pjoin

import pytest

import datagristle.file_sorter as mod
import datagristle.csvhelper as csvhelper



class TestSortKeyRecord(object):

    def test_happypath(self):
        sort_key_rec= mod.SortKeyRecord('5sr')
        assert sort_key_rec.position == 5
        assert sort_key_rec.type == 'str'
        assert sort_key_rec.order == 'reverse'

    def test_case(self):
        sort_key_rec= mod.SortKeyRecord('5SR')
        assert sort_key_rec.position == 5
        assert sort_key_rec.type == 'str'
        assert sort_key_rec.order == 'reverse'

    def test_big_position(self):
        sort_key_rec= mod.SortKeyRecord('99SR')
        assert sort_key_rec.position == 99
        assert sort_key_rec.type == 'str'
        assert sort_key_rec.order == 'reverse'

    def test_all_types(self):
        sort_key_rec= mod.SortKeyRecord('99SR')
        assert sort_key_rec.type == 'str'

        sort_key_rec= mod.SortKeyRecord('99iR')
        assert sort_key_rec.type == 'int'

        sort_key_rec= mod.SortKeyRecord('99fR')
        assert sort_key_rec.type == 'float'

    def test_all_orders(self):
        sort_key_rec= mod.SortKeyRecord('99SR')
        assert sort_key_rec.order == 'reverse'

        sort_key_rec= mod.SortKeyRecord('99if')
        assert sort_key_rec.order == 'forward'

    def test_invalid_position(self):
        with pytest.raises(ValueError):
            sort_key_rec= mod.SortKeyRecord('bSR')

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            sort_key_rec= mod.SortKeyRecord('99R')

    def test_invalid_order(self):
        with pytest.raises(ValueError):
            sort_key_rec= mod.SortKeyRecord('9i9')



class TestSortkeysConfig(object):

    def test_one_key(self):
        sort_keys = mod.SortKeysConfig(['1sf'])
        assert sort_keys.key_fields == [mod.SortKeyRecord('1sf')]

    def test_two_keys(self):
        sort_keys = mod.SortKeysConfig(['1sf','2ir'])
        assert sort_keys.key_fields == [mod.SortKeyRecord('1sf'), mod.SortKeyRecord('2ir')]

    def test_multi_string_orders(self):
        sort_keys = mod.SortKeysConfig(['1sf','2sr'])
        assert sort_keys.multi_string_orders() is True

        sort_keys = mod.SortKeysConfig(['1sf','2sf'])
        assert sort_keys.multi_string_orders() is False

    def test_get_primary_order(self):
        sort_keys = mod.SortKeysConfig(['1sf','2ir'])
        assert sort_keys.get_primary_order() == 'forward'

        sort_keys = mod.SortKeysConfig(['1sr','2sr'])
        assert sort_keys.get_primary_order() == 'reverse'

        sort_keys = mod.SortKeysConfig(['1ir'])
        assert sort_keys.get_primary_order() == 'reverse'

    def test_get_sort_fields(self):
        sort_keys = mod.SortKeysConfig(['1sf','2ir'])
        assert sort_keys.get_sort_fields() == [0,1]



class TestCSVPythonSorter(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, has_header=False)
        self.fqfn  = create_test_file(self.temp_dir)
        self.out_dir = tempfile.mkdtemp(prefix='gristle_out_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.out_dir)

    def test_sort_file_string(self):
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0sf'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=False)
        stats = sorter.sort_file()
        pp(sorter.stats)
        sorter.close()
        with open(out_fqfn, newline='') as buf:
            reader = csv.reader(buf)
            data = list(reader)
        pp(data)
        assert data[0][0] == '1'
        assert data[1][0] == '2'
        assert data[2][0] == '3'
        assert data[3][0] == '4'

    def test_sort_file_numeric(self):
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0if'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=False)
        stats = sorter.sort_file()
        pp(sorter.stats)
        sorter.close()
        with open(out_fqfn, newline='') as buf:
            reader = csv.reader(buf)
            data = list(reader)
        pp(data)
        assert data[0][0] == '1'
        assert data[1][0] == '2'
        assert data[2][0] == '3'
        assert data[3][0] == '4'

    def test_sort_file_reverse(self):
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0ir'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=False)
        stats = sorter.sort_file()
        pp(sorter.stats)
        sorter.close()
        with open(out_fqfn, newline='') as buf:
            reader = csv.reader(buf)
            data = list(reader)
        pp(data)
        assert data[0][0] == '4'
        assert data[1][0] == '3'
        assert data[2][0] == '2'
        assert data[3][0] == '1'

    def test_sort_file_dedup(self):
        self.fqfn  = create_test_file(self.temp_dir, duplicate=True)
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0ir'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=True)
        stats = sorter.sort_file()
        pp(sorter.stats)
        sorter.close()
        with open(out_fqfn, newline='') as buf:
            reader = csv.reader(buf)
            data = list(reader)
        pp(data)
        assert sorter.stats['recs_read'] == 5
        assert sorter.stats['recs_written'] == 4
        assert sorter.stats['recs_deduped'] == 1
        assert data[0][0] == '4'
        assert data[1][0] == '3'
        assert data[2][0] == '2'
        assert data[3][0] == '1'

    def test_header(self):
        self.fqfn  = create_test_file(self.temp_dir, header=True)
        self.dialect.has_header = True
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0if'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=True)
        stats = sorter.sort_file()
        pp(sorter.stats)
        sorter.close()
        with open(out_fqfn, newline='') as buf:
            reader = csv.reader(buf)
            data = list(reader)
        pp(data)
        assert sorter.stats['recs_read'] == 5
        assert sorter.stats['recs_written'] == 5
        assert sorter.stats['recs_deduped'] == 0
        assert data[0][0] == 'num'
        assert data[1][0] == '1'
        assert data[2][0] == '2'
        assert data[3][0] == '3'
        assert data[4][0] == '4'


    def test_get_sort_values_happy_path(self):
        self.fqfn  = create_test_file(self.temp_dir, header=True)
        self.dialect.has_header = True
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0sf'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=True)

        rec = ['foo', 3, 'bar', 9]
        primary_order = 'forward'
        assert sorter._get_sort_values(sort_keys_config.key_fields, rec, primary_order) == ['foo']


    def test_get_sort_values_(self):
        self.fqfn = create_test_file(self.temp_dir, header=True)
        self.dialect.has_header = True
        out_fqfn = self.fqfn + '.sorted'
        sort_keys_config = mod.SortKeysConfig(['0sf', '1ir'])
        sorter = mod.CSVPythonSorter(self.fqfn, out_fqfn, sort_keys_config, self.dialect, dedupe=True)

        rec = ['foo', 3, 'bar', 9]
        primary_order = 'forward'
        pp(sorter._get_sort_values(sort_keys_config.key_fields, rec, primary_order))
        assert sorter._get_sort_values(sort_keys_config.key_fields, rec, primary_order) == ['foo', -3]



class TestIsDuplicate(object):

    def test_deduper(self):

        assert not mod.isduplicate('a')
        assert not mod.isduplicate('b')
        assert not mod.isduplicate('c')
        assert mod.isduplicate('c')
        assert mod.isduplicate('c')
        assert not mod.isduplicate('d')

    def test_deduper_with_tuple_input(self):

        assert not mod.isduplicate(('a',))
        assert not mod.isduplicate(('b',))
        assert not mod.isduplicate(('c',))
        assert mod.isduplicate(('c',))
        assert mod.isduplicate(('c',))
        assert not mod.isduplicate(('d',))



class TestTransform(object):

    def test_string(self):
        sort_key_rec = mod.SortKeyRecord('2sf')
        assert mod.transform('foo', sort_key_rec, 'forward') == 'foo'

    def test_integer(self):
        sort_key_rec = mod.SortKeyRecord('2if')
        assert mod.transform('3', sort_key_rec, 'forward') == 3

    def test_integer_reversed(self):
        sort_key_rec = mod.SortKeyRecord('2ir')
        assert mod.transform('3', sort_key_rec, 'forward') == -3

    def test_integer_reversed_but_primary_is_already_reverse(self):
        sort_key_rec = mod.SortKeyRecord('2ir')
        assert mod.transform('3', sort_key_rec, 'reversed') == 3

    def test_float(self):
        sort_key_rec = mod.SortKeyRecord('2ff')
        assert mod.transform('3.2', sort_key_rec, 'forward') == 3.2

    def test_float_reversed(self):
        sort_key_rec = mod.SortKeyRecord('2fr')
        assert mod.transform('3.2', sort_key_rec, 'forward') == -3.2

    def test_float_reversed_but_primary_is_already_reverse(self):
        sort_key_rec = mod.SortKeyRecord('2fr')
        assert mod.transform('3.2', sort_key_rec, 'reversed') == 3.2

    def test_string_reversed(self):
        sort_key_rec = mod.SortKeyRecord('2sr')
        assert mod.transform('3.2', sort_key_rec, 'forward') == '3.2'

    def test_string_reversed_but_primary_is_already_reverse(self):
        sort_key_rec = mod.SortKeyRecord('2sr')
        assert mod.transform('3.2', sort_key_rec, 'reversed') == '3.2'




class TestSort(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')
        self.dialect = csvhelper.Dialect(delimiter=',', quoting=csv.QUOTE_NONE, has_header=False)
        self.fqfn  = create_test_file(self.temp_dir)
        self.out_dir = tempfile.mkdtemp(prefix='gristle_out_')

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.out_dir)

    def test_sort_file_invalid_inputs(self):
        with pytest.raises(AssertionError):
            sorter = mod.CSVSorter(self.dialect, None)
        sorter = mod.CSVSorter(self.dialect, '3')
        with pytest.raises(ValueError):
            sorter.sort_file('/tmp/thisfiledoesnotexist.csv')

    def test_sort_file_numeric(self):
        join_fields = '0'
        sorter = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '1'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            elif fileinput.lineno() == 3:
                assert fields[0] == '3'
            elif fileinput.lineno() == 4:
                assert fields[0] == '4'
            else:
                assert 0, 'too many rows returned'
        fileinput.close()

    def test_sort_big_file_numeric(self):
        join_fields = '0'
        sorter = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '1'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            elif fileinput.lineno() == 3:
                assert fields[0] == '3'
            elif fileinput.lineno() == 4:
                assert fields[0] == '4'
            elif fileinput.lineno() == 5:
                assert fields[0] == '5'
            elif fileinput.lineno() == 6:
                assert fields[0] == '6'
            elif fileinput.lineno() == 7:
                assert fields[0] == '7'
            elif fileinput.lineno() == 8:
                assert fields[0] == '8'
            elif fileinput.lineno() == 9:
                assert fields[0] == '9'
            elif fileinput.lineno() == 10:
                assert fields[0] == '10'
            else:
                assert 0, 'too many rows returned'
        fileinput.close()

    def test_sort_file_with_tab_delimiter(self):
        join_fields = '0'
        self.dialect.delimiter = '\t'
        self.fqfn = create_test_file(self.temp_dir, self.dialect.delimiter)
        sorter = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(self.dialect.delimiter)
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '1'
            elif fileinput.lineno() == 2:
                assert fields[0] == '2'
            elif fileinput.lineno() == 3:
                assert fields[0] == '3'
            elif fileinput.lineno() == 4:
                assert fields[0] == '4'
            else:
                assert 0, 'too many rows returned'
        fileinput.close()

    def test_sort_file_alpha_combo(self):
        join_fields = [1, 2]
        sorter = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.temp_dir)
        outfile = sorter.sort_file(self.fqfn)
        assert outfile == self.fqfn + '.sorted'
        for rec in fileinput.input(self.fqfn + '.sorted'):
            fields = rec.split(',')
            print(fields)
            if fileinput.lineno() == 1:
                assert fields[0] == '4'
            elif fileinput.lineno() == 2:
                assert fields[0] == '3'
            elif fileinput.lineno() == 3:
                assert fields[0] == '2'
            elif fileinput.lineno() == 4:
                assert fields[0] == '1'
            else:
                assert 0, 'too many rows returns'
        fileinput.close()

    def test_sort_file_outdir(self):
        join_fields = [1, 2]
        sorter = mod.CSVSorter(self.dialect, join_fields, self.temp_dir, self.out_dir)
        outfile = sorter.sort_file(self.fqfn)
        assert dirname(outfile) == self.out_dir
        assert basename(outfile) == basename(self.fqfn) + '.sorted'


def create_test_file(temp_dir, delimiter=',', duplicate=False, header=False):
    fqfn = pjoin(temp_dir, 'foo.csv')
    with open(fqfn, 'w') as f:
        if header:
            f.write(delimiter.join(['num', 'alpha', 'alphanumeric']) + '\n')
        f.write(delimiter.join(['4', 'aaa', 'a23']) + '\n')
        f.write(delimiter.join(['2', 'bbb', 'a23']) + '\n')
        f.write(delimiter.join(['1', 'bbb', 'b23']) + '\n')
        f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
        if duplicate:
            f.write(delimiter.join(['3', 'aaa', 'b23']) + '\n')
    return fqfn
