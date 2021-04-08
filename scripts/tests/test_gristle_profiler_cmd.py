#!/usr/bin/env python
""" Tests gristle_profiler.py

    Contains a primary class: FileStructureFixtureManager
    Which is extended by six classes that override various methods or variables.
    This is a failed experiment - since the output isn't as informative as it
    should be.  This should be redesigned.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use
#pylint: disable=empty-docstring

import csv
import errno
import os
import shutil
import tempfile
from os.path import join as pjoin, dirname
from pprint import pprint as pp

import envoy
import pytest

import datagristle.csvhelper as csvhelper
import datagristle.test_tools as test_tools

script_path = dirname(dirname(os.path.realpath((__file__))))



def generate_test_file(delim, rec_list, quoted=False, dir_name=None):
    if dir_name:
        (file_desc, fqfn) = tempfile.mkstemp(dir=dir_name)
    else:
        (file_desc, fqfn) = tempfile.mkstemp()
    fileobj = os.fdopen(file_desc, "w")

    for rec in rec_list:
        if quoted:
            for i in range(len(rec)):
                rec[i] = '"%s"' % rec[i]
        outrec = delim.join(rec)+'\n'
        pp(outrec)
        fileobj.write(outrec)

    fileobj.close()
    return fqfn


def get_value(parsable_out, division, section, subsection, key):
    """ Gets the value (right-most field) out of gristle_profiler
        parsable output given the key values for the rest of the fields.
    """
    mydialect = csv.Dialect
    mydialect.delimiter = '|'
    mydialect.quoting = csvhelper.get_quote_number('QUOTE_ALL')
    mydialect.quotechar = '"'
    mydialect.lineterminator = '\n'

    csvobj = csv.reader(parsable_out.split('\n'), dialect=mydialect)
    for record in csvobj:
        if not record:
            continue
        assert len(record) == 5
        rec_division = record[0]
        rec_section = record[1]
        rec_subsection = record[2]
        rec_key = record[3]
        rec_value = record[4]

        if (rec_division == division
                and rec_section == section
                and rec_subsection == subsection
                and rec_key == key):
            return rec_value

    return None



class TestEmptyFile(object):
    """ Temporarily suppressing - I think the problem is that the behavior for handling empty files was changed with the
    new config
    """

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='datagristle_deter_')

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def create_empty_file_with_header(self, fqfn):
        with open(fqfn, 'w') as fileobj:
            fileobj.write('col1, colb2, col3')

    def test_empty_file(self):
        fqfn = pjoin(self.tmp_dir, 'empty.csv')
        test_tools.touch(fqfn)
        cmd = '%s --infiles %s --output-format=parsable' % (pjoin(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == errno.ENODATA
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'record_count')  is None
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'has_header')    is None

    def test_empty_file_with_header(self):
        fqfn = os.path.join(self.tmp_dir, 'empty_header.csv')
        self.create_empty_file_with_header(fqfn)
        cmd = '%s --infiles %s --output-format=parsable' % (pjoin(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'record_count') == '1'
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'has_header') == 'True'

    def test_empty_file_with_header_and_hasheader_arg(self):
        fqfn = os.path.join(self.tmp_dir, 'empty_header.csv')
        self.create_empty_file_with_header(fqfn)
        cmd = '%s --infiles %s --output-format=parsable --has-header' % (pjoin(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'record_count') == '1'
        assert get_value(runner.std_out, 'file_analysis_results', 'main', 'main', 'has_header') == 'True'





class TestOutputFormattingAndContents(object):

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='datagristle_deter_')
        recs = [['Alabama', '8', '18'],
                ['Alaska', '6', '16'],
                ['Arizona', '6', '14'],
                ['Arkansas', '2', '12'],
                ['California', '19', '44']]
        self.file_struct = {}
        self.field_struct = {}

        fqfn = generate_test_file(delim='|', rec_list=recs, quoted=False, dir_name=self.tmp_dir)
        cmd = '%s --infiles %s --output-format=parsable' % (os.path.join(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0

        mydialect = csv.Dialect
        mydialect.delimiter = '|'
        mydialect.quoting = csvhelper.get_quote_number('QUOTE_ALL')
        mydialect.quotechar = '"'
        mydialect.lineterminator = '\n'

        csvobj = csv.reader(runner.std_out.split('\n'), dialect=mydialect)
        for record in csvobj:
            if not record:
                continue
            assert len(record) == 5
            division = record[0]
            section = record[1]
            subsection = record[2]
            key = record[3]
            value = record[4]

            assert division in ['file_analysis_results', 'field_analysis_results']

            if division == 'file_analysis_results':
                assert section == 'main'
                assert subsection == 'main'
                self.file_struct[key] = value
            elif division == 'field_analysis_results':
                assert 'field_' in section
                assert subsection in ['main', 'top_values']
                if section not in self.field_struct:
                    self.field_struct[section] = {}
                if subsection not in self.field_struct[section]:
                    self.field_struct[section][subsection] = {}
                self.field_struct[section][subsection][key] = value

    def teardown_method(self, teardown):
        shutil.rmtree(self.tmp_dir)

    def test_file_info(self):
        pp(self.file_struct)
        assert self.file_struct['record_count'] == '5'
        assert self.file_struct['skipinitialspace'] == 'False'
        assert self.file_struct['quoting'] == 'QUOTE_NONE'
        assert self.file_struct['field_count'] == '3'
        assert self.file_struct['delimiter'] == "'|'"
        assert self.file_struct['has_header'] == 'False'
        assert self.file_struct['escapechar'] == 'None'
        assert self.file_struct['doublequote'] == 'False'

    def test_field_info(self):
        assert self.field_struct['field_0']['main']['field_number'] == '0'
        assert self.field_struct['field_0']['main']['name'] == 'field_0'
        assert self.field_struct['field_0']['main']['type'] == 'string'
        assert self.field_struct['field_0']['main']['known_values'] == '5'
        assert self.field_struct['field_0']['main']['min'] == 'Alabama'
        assert self.field_struct['field_0']['main']['max'] == 'California'
        assert self.field_struct['field_0']['main']['unique_values'] == '5'
        assert self.field_struct['field_0']['main']['wrong_field_cnt'] == '0'
        assert self.field_struct['field_0']['main']['case'] == 'mixed'
        assert self.field_struct['field_0']['main']['max_length'] == '10'
        assert self.field_struct['field_0']['main']['mean_length'] == '7.6'
        assert self.field_struct['field_0']['main']['min_length'] == '6'

        assert self.field_struct['field_1']['main']['field_number'] == '1'
        assert self.field_struct['field_1']['main']['name'] == 'field_1'
        assert self.field_struct['field_1']['main']['type'] == 'integer'
        assert self.field_struct['field_1']['main']['known_values'] == '4'
        assert self.field_struct['field_1']['main']['min'] == '2'
        assert self.field_struct['field_1']['main']['max'] == '19'
        assert self.field_struct['field_1']['main']['unique_values'] == '4'
        assert self.field_struct['field_1']['main']['wrong_field_cnt'] == '0'
        assert self.field_struct['field_1']['main']['mean'] == '8.2'
        assert self.field_struct['field_1']['main']['median'] == '6.0'
        assert self.field_struct['field_1']['main']['std_dev'] == '5.74108003776293'
        assert self.field_struct['field_1']['main']['variance'] == '32.96'

    def test_top_value_info(self):
        pp(self.field_struct)
        assert self.field_struct['field_0']['top_values']['top_values'] == 'not shown - all are unique'
        assert self.field_struct['field_1']['top_values']['2'] == '1'
        assert self.field_struct['field_1']['top_values']['6'] == '2'
        assert self.field_struct['field_1']['top_values']['8'] == '1'
        assert self.field_struct['field_1']['top_values']['19'] == '1'



class TestReadLimit(object):

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='datagristle_deter_')
        recs = [['Alabama', '8', '18'],
                ['Alaska', '6', '16'],
                ['Arizona', '6', '14'],
                ['Arkansas', '2', '12'],
                ['California', '19', '44'],
                ['Colorado', '19', '44'],
                ['Illinois', '19', '44'],
                ['Indiana', '19', '44'],
                ['Kansas', '19', '44'],
                ['Kentucky', '19', '44'],
                ['Louisiana', '19', '44'],
                ['Maine', '19', '44'],
                ['Mississippi', '19', '44'],
                ['Nebraska', '19', '44'],
                ['Oklahoma', '19', '44'],
                ['Tennessee', '19', '44'],
                ['Texas', '19', '9999'],
                ['Virginia', '19', '44'],
                ['West Virginia', '19', '44']]
        self.file_struct = {}
        self.field_struct = {}

        fqfn = generate_test_file(delim='|', rec_list=recs, quoted=False, dir_name=self.tmp_dir)
        cmd = '%s \
               --infiles %s \
               --read-limit 4 \
               --output-format=parsable' % (os.path.join(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0

        mydialect = csv.Dialect
        mydialect.delimiter = '|'
        mydialect.quoting = csvhelper.get_quote_number('QUOTE_ALL')
        mydialect.quotechar = '"'
        mydialect.lineterminator = '\n'

        csvobj = csv.reader(runner.std_out.split('\n'), dialect=mydialect)
        for record in csvobj:
            if not record:
                continue
            assert len(record) == 5
            division = record[0]
            section = record[1]
            subsection = record[2]
            key = record[3]
            value = record[4]

            assert division in ['file_analysis_results', 'field_analysis_results']

            if division == 'file_analysis_results':
                assert section == 'main'
                assert subsection == 'main'
                self.file_struct[key] = value
            elif division == 'field_analysis_results':
                assert 'field_' in section
                assert subsection in ['main', 'top_values']
                if section not in self.field_struct:
                    self.field_struct[section] = {}
                if subsection not in self.field_struct[section]:
                    self.field_struct[section][subsection] = {}
                self.field_struct[section][subsection][key] = value

    def teardown_method(self, teardown):
        shutil.rmtree(self.tmp_dir)

    def test_limits(self):
        assert 'est' in self.file_struct['record_count']

    def test_file_info(self):
        assert self.file_struct['skipinitialspace'] == 'False'
        assert self.file_struct['quoting'] == 'QUOTE_NONE'
        assert self.file_struct['field_count'] == '3'
        assert self.file_struct['delimiter'] == "'|'"

    def test_field_info(self):
        assert self.field_struct['field_0']['main']['known_values'] == '4'
        assert self.field_struct['field_0']['main']['min'] == 'Alabama'
        assert self.field_struct['field_0']['main']['max'] == 'Arkansas'
        assert self.field_struct['field_0']['main']['unique_values'] == '4'



class TestMaxFreq(object):

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='datagristle_deter_')
        recs = [['Alabama', '8', '18'],
                ['Alaska', '6', '16'],
                ['Arizona', '6', '14'],
                ['Arkansas', '2', '12'],
                ['California', '19', '44'],
                ['Colorado', '19', '44'],
                ['Illinois', '19', '44'],
                ['Indiana', '19', '44'],
                ['Kansas', '19', '44'],
                ['Kentucky', '19', '44'],
                ['Louisiana', '19', '44'],
                ['Maine', '19', '44'],
                ['Mississippi', '19', '44'],
                ['Nebraska', '19', '44'],
                ['Oklahoma', '19', '44'],
                ['Tennessee', '19', '44'],
                ['Texas', '19', '9999'],
                ['Virginia', '19', '44'],
                ['West Virginia', '19', '44']]
        self.file_struct = {}
        self.field_struct = {}

        fqfn = generate_test_file(delim='|', rec_list=recs, quoted=False, dir_name=self.tmp_dir)
        cmd = '%s \
               --infiles %s \
               --max-freq 10  \
               --output-format=parsable' % (os.path.join(script_path, 'gristle_profiler'), fqfn)
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == 0

        mydialect = csv.Dialect
        mydialect.delimiter = '|'
        mydialect.quoting = csvhelper.get_quote_number('QUOTE_ALL')
        mydialect.quotechar = '"'
        mydialect.lineterminator = '\n'

        csvobj = csv.reader(runner.std_out.split('\n'), dialect=mydialect)
        for record in csvobj:
            if not record:
                continue
            if len(record) != 5:
                if 'WARNING: freq dict is too large' in record[0]:
                    continue # ignore warning row
                else:
                    pytest.fail('Invalid result record: %s' % record[0])

            division = record[0]
            section = record[1]
            subsection = record[2]
            key = record[3]
            value = record[4]
            assert division in ['file_analysis_results', 'field_analysis_results']

            if division == 'file_analysis_results':
                assert section == 'main'
                assert subsection == 'main'
                self.file_struct[key] = value
            elif division == 'field_analysis_results':
                assert 'field_' in section
                assert subsection in ['main', 'top_values']
                if section not in self.field_struct:
                    self.field_struct[section] = {}
                if subsection not in self.field_struct[section]:
                    self.field_struct[section][subsection] = {}
                self.field_struct[section][subsection][key] = value

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def test_limits(self):
        assert self.file_struct['record_count'] == '19'

    def test_field_info(self):
        assert self.field_struct['field_0']['main']['known_values'] == '10'
        assert self.field_struct['field_0']['main']['min'] == 'Alabama'
        assert self.field_struct['field_0']['main']['max'] == 'Kentucky' # affected
        assert self.field_struct['field_0']['main']['unique_values'] == '10' # affected
