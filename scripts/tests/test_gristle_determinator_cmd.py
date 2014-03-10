#!/usr/bin/env python
""" Tests gristle_determinator.py

    Contains a primary class: FileStructureFixtureManager
    Which is extended by six classes that override various methods or variables.
    This is a failed experiment - since the output isn't as informative as it
    should be.  This should be redesigned.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013 Ken Farmer
"""
import sys
import os
import tempfile
import envoy
import csv
import pytest
import errno
from pprint import pprint as pp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')

import gristle.file_type as file_type
script_path = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))



def generate_test_file(delim, rec_list, quoted=False):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w")

    for rec in rec_list:
        if quoted:
            for i in range(len(rec)):
                rec[i] = '"%s"' % rec[i]
        outrec = delim.join(rec)+'\n'
        fp.write(outrec)

    fp.close()
    return fqfn


def get_value(parsable_out, division, section, subsection, key):
    """ Gets the value (right-most field) out of gristle_determinator
        parsable output given the key values for the rest of the fields.
    """
    mydialect                = csv.Dialect
    mydialect.delimiter      = '|'
    mydialect.quoting        = file_type.get_quote_number('QUOTE_ALL')
    mydialect.quotechar      = '"'
    mydialect.lineterminator = '\n'

    csvobj = csv.reader(parsable_out.split('\n'), dialect=mydialect)

    for record in csvobj:
        if not record:
            continue
        assert len(record) == 5
        rec_division   = record[0]
        rec_section    = record[1]
        rec_subsection = record[2]
        rec_key        = record[3]
        rec_value      = record[4]

        if (rec_division   == division
        and rec_section    == section
        and rec_subsection == subsection
        and rec_key        == key):
            return rec_value

    return None



class Test_empty_file(object):

    def setup_method(self, method):
        pass

    def test_empty_file(self):
        fqfn = os.path.join(data_dir, 'empty.csv')
        cmd = '%s %s --outputformat=parsable' % (os.path.join(script_path, 'gristle_determinator'), fqfn)
        r    = envoy.run(cmd)
        print r.std_out
        print r.std_err
        assert r.status_code == errno.ENODATA
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'record_count')  is None
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'hasheader')     is None

    def test_empty_file_with_header(self):
        fqfn = os.path.join(data_dir, 'empty_header.csv')
        cmd = '%s %s --outputformat=parsable' % (os.path.join(script_path, 'gristle_determinator'), fqfn)
        r    = envoy.run(cmd)
        print r.std_out
        print r.std_err
        assert r.status_code == 0
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'record_count')  == '1'
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'hasheader')     == 'True'

    def test_empty_file_with_header_and_hasheader_arg(self):
        fqfn = os.path.join(data_dir, 'empty_header.csv')
        cmd = '%s %s --outputformat=parsable --hasheader' % (os.path.join(script_path, 'gristle_determinator'), fqfn)
        r    = envoy.run(cmd)
        print r.std_out
        print r.std_err
        assert r.status_code == 0
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'record_count')  == '1'
        assert get_value(r.std_out, 'file_analysis_results', 'main', 'main', 'hasheader')     == 'True'





class Test_output_formatting_and_contents(object):

    def setup_method(self, method):
        recs = [ ['Alabama','8','18'],
                 ['Alaska','6','16'],
                 ['Arizona','6','14'],
                 ['Arkansas','2','12'],
                 ['California','19','44'] ]
        self.file_struct  = {}
        self.field_struct = {}

        fqfn = generate_test_file(delim='|', rec_list=recs, quoted=False)
        cmd = '%s %s --outputformat=parsable' % (os.path.join(script_path, 'gristle_determinator'), fqfn)
        r    = envoy.run(cmd)
        #print r.std_out
        #print r.std_err
        assert r.status_code == 0

        mydialect                = csv.Dialect
        mydialect.delimiter      = '|'
        mydialect.quoting        = file_type.get_quote_number('QUOTE_ALL')
        mydialect.quotechar      = '"'
        mydialect.lineterminator = '\n'

        csvobj = csv.reader(r.std_out.split('\n'), dialect=mydialect)
        for record in csvobj:
            if not record:
                continue
            assert len(record) == 5
            division   = record[0]
            section    = record[1]
            subsection = record[2]
            key        = record[3]
            value      = record[4]

            assert division in ['file_analysis_results','field_analysis_results']

            if division == 'file_analysis_results':
                assert section    == 'main'
                assert subsection == 'main'
                self.file_struct[key] = value
            elif division == 'field_analysis_results':
                assert 'field_' in section
                assert subsection in ['main','top_values']
                if section not in self.field_struct:
                    self.field_struct[section] = {}
                if subsection not in self.field_struct[section]:
                    self.field_struct[section][subsection] = {}
                self.field_struct[section][subsection][key] = value


    def test_file_info(self):
        assert self.file_struct['record_count']      == '5'
        assert self.file_struct['skipinitialspace']  == 'False'
        assert self.file_struct['quoting']           == 'QUOTE_NONE'
        assert self.file_struct['field_count']       == '3'
        assert self.file_struct['delimiter']         == "'|'"
        assert self.file_struct['hasheader']         == 'False'
        assert self.file_struct['escapechar']        == 'None'
        assert self.file_struct['csv_quoting']       == 'False'
        assert self.file_struct['doublequote']       == 'False'
        assert self.file_struct['format_type']       == 'csv'

    def test_field_info(self):
        assert self.field_struct['field_0']['main']['field_number']    == '0'
        assert self.field_struct['field_0']['main']['name']            == 'field_0'
        assert self.field_struct['field_0']['main']['type']            == 'string'
        assert self.field_struct['field_0']['main']['known_values']    == '5'
        assert self.field_struct['field_0']['main']['min']             == 'Alabama'
        assert self.field_struct['field_0']['main']['max']             == 'California'
        assert self.field_struct['field_0']['main']['unique_values']   == '5'
        assert self.field_struct['field_0']['main']['wrong_field_cnt'] == '0'
        assert self.field_struct['field_0']['main']['case']            == 'mixed'
        assert self.field_struct['field_0']['main']['max_length']      == '10'
        assert self.field_struct['field_0']['main']['mean_length']     == '7.6'
        assert self.field_struct['field_0']['main']['min_length']      == '6'

        assert self.field_struct['field_1']['main']['field_number']    == '1'
        assert self.field_struct['field_1']['main']['name']            == 'field_1'
        assert self.field_struct['field_1']['main']['type']            == 'integer'
        assert self.field_struct['field_1']['main']['known_values']    == '4'
        assert self.field_struct['field_1']['main']['min']             == '2'
        assert self.field_struct['field_1']['main']['max']             == '19'
        assert self.field_struct['field_1']['main']['unique_values']   == '4'
        assert self.field_struct['field_1']['main']['wrong_field_cnt'] == '0'
        assert self.field_struct['field_1']['main']['mean']            == '8.2'
        assert self.field_struct['field_1']['main']['median']          == '6.0'
        assert self.field_struct['field_1']['main']['std_dev']         == '5.74108003776'
        assert self.field_struct['field_1']['main']['variance']        == '32.96'

    def test_top_value_info(self):
        #pp(self.field_struct)
        assert self.field_struct['field_0']['top_values']['top_values']  == 'not shown - all are unique'
        assert self.field_struct['field_1']['top_values']['2']    == '1'
        assert self.field_struct['field_1']['top_values']['6']    == '2'
        assert self.field_struct['field_1']['top_values']['8']    == '1'
        assert self.field_struct['field_1']['top_values']['19']   == '1'


