#!/usr/bin/env python
""" To do:
      1.  test with multiple input files

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import time
import fileinput
import pytest
import glob
import errno
from pprint import pprint as pp

import envoy
import yaml

#--- gristle modules -------------------
import test_tools

# get pathing set for running code out of project structure & testing it via tox
data_dir    = os.path.join(test_tools.get_app_root(), 'data')
script_dir  = os.path.dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm      = os.path.join(script_dir, 'gristle_validator')
sys.path.insert(0, test_tools.get_app_root())

import gristle.common  as comm
from gristle.common import dict_coalesce



def _generate_foobarbatz_file(recs, delimiter=False):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorIn_')
    fp         = os.fdopen(fd,"w")
    for rec in range(recs):
        if delimiter:
            rec = '"foo"|"bar"|"batz"|"1.9"|"2"|"%d"' % rec
        else:
            rec = 'foo|bar|batz|1.9|2|%d' % rec
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn


def _generate_foobarbatz_schema():
    schema    = {'items': []}
    field0    = {'title':     'foo',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'enum':      ['foo']}
    schema['items'].append(field0)
    field1    = {'title':     'bar',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True}
    schema['items'].append(field1)
    field2    = {'title':     'batz',
                 'blank':     False,
                 'minLength': 4,
                 'maxLength': 4,
                 'required':  True}
    schema['items'].append(field2)
    field3    = {'title':     'field3',
                 'blank':     False,
                 'required':  True,
                 'dg_type':   'float',
                 'dg_minimum': 1,
                 'dg_maximum': 2}
    schema['items'].append(field3)
    field4    = {'title':     'field4',
                 'blank':     False,
                 'required':  True,
                 'dg_type':   'integer',
                 'dg_minimum': 1,
                 'dg_maximum': 99}
    schema['items'].append(field4)
    field5    = {'title':     'rowcnt',
                 'blank':     False,
                 'required':  True,
                 'dg_type':   'integer',
                 'dg_minimum': '0',
                 'dg_maximum': 9999999}
    schema['items'].append(field5)
    return schema


def _write_schema_file(name, schema):
    temp_fqfn = '/tmp/test_gristle_validator_%s_schema.yml' % name
    with open(temp_fqfn, 'w') as schema_file:
        schema_file.write(yaml.dump(schema))
    return temp_fqfn



def _generate_7x7_schema_file():
    schema    = {'items': []}
    col0      = {'title':     'col0',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col0)
    col1      = {'title':     'col1',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col1)
    col2      = {'title':     'col2',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col2)
    col3      = {'title':     'col3',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col3)
    col4      = {'title':     'col4',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col4)
    col5      = {'title':     'col5',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col5)
    col6      = {'title':     'col6',
                 'blank':     False,
                 'minLength': 3,
                 'maxLength': 3,
                 'required':  True,
                 'pattern':   '\\b\d-\d'}
    schema['items'].append(col6)

    return _write_schema_file('7x7', schema)




class TestFieldCount(object):
    """ Tests gristle_validator functionality involved in verifying
        that all records within a file have the correct number of fields.
    """


    def setup_method(self, method):

        self.pgm                   = fq_pgm
        self.std_7x7_fqfn, self.data_7x7  = test_tools.generate_7x7_test_file('TestGristleValidator7x7In_')
        (dummy, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_')
        (dummy, self.outerr_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_')

    def teardown_method(self, method):
        test_tools.temp_file_remover(self.std_7x7_fqfn)
        test_tools.temp_file_remover(self.outgood_fqfn)
        test_tools.temp_file_remover(self.outerr_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestGristleValidator'))


    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out     = response.std_out
        self.std_err     = response.std_err
        self.good_output = good_recs
        self.err_output  = err_recs



    def test_good_field_cnt(self):

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --quoting 'quote_none'    \
                         --fieldcnt 7              \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                   """ % {'pgm': self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print '\n command: %s' % self.cmd

        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 7
        assert self.good_output      == self.data_7x7


    def test_field_cnt_default(self):
        """ Test running without a field_cnt
        """

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                   """ % {'pgm': self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code     == 0
        assert len(self.err_output) == 0
        assert self.good_output     == self.data_7x7


    def test_bad_field_cnt(self):

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 70             \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code      == errno.EBADMSG
        assert len(self.err_output)  == 7
        assert len(self.good_output) == 0

        orig_recs = []
        for rec in self.err_output:
            fields = rec.split('|')
            assert len(fields) == 8  # extra field for msg
            orig_recs.append('|'.join(fields[:7]))
        assert orig_recs == self.data_7x7


    def test_silent_option(self):
        """ The silent option will force all writes to be bypassed.
        """

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 7              \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --silent                  \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 0
        assert len(self.std_out)     == 0
        # std_err should be 0, but coverage.py might write 46 bytes
        # to it:
        assert (len(self.std_err)    == 0
                or (len(self.std_err) < 50
                    and 'Coverage.py' in self.std_err))



    def test_stats_option(self):
        """ The stats option will create a report to stdout
            The stats should look like this:
                input_cnt        | 7
                invalid_cnt      | 7
                valid_cnt        | 0
        """
        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 70             \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --stats                   \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code == errno.EBADMSG
        assert len(self.err_output)  >  0
        assert len(self.good_output) == 0
        assert len(self.std_out)     >  0
        assert len(self.std_out)     >  0
        # std_err should be 0, but coverage.py might write 46 bytes
        # to it:
        assert (len(self.std_err)    == 0
                or (len(self.std_err) < 50
                    and 'Coverage.py' in self.std_err))

        std_out_recs = self.std_out.split('\n')
        input_cnt_found   = False
        invalid_cnt_found = False
        valid_cnt_found   = False

        for rec in std_out_recs:
            if not rec:
                continue
            fields = rec.split('|')
            assert len(fields) == 2

            if fields[0].strip() == 'input_cnt':
                assert fields[1].strip() == '7'
                input_cnt_found = True
            elif fields[0].strip() == 'invalid_cnt':
                assert fields[1].strip() == '7'
                invalid_cnt_found = True
            elif fields[0].strip() == 'valid_cnt':
                assert fields[1].strip() == '0'
                valid_cnt_found = True

        assert input_cnt_found
        assert invalid_cnt_found
        assert valid_cnt_found


    def test_randomout_100(self):
        in_fqfn = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 6              \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --randomout 100           \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 10000


    def test_randomout_0(self):
        in_fqfn = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 6              \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --randomout 0             \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 0


    def test_randomout_10(self):

        in_fqfn = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 6              \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --randomout 10            \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err

        assert self.status_code == 0
        assert len(self.err_output)  == 0
        assert (0.2 * 100000) > len(self.good_output) > (0.05 * 10000)



class TestEmptyFile(object):

    def setup_method(self, method):
        self.empty_fqfn            = self._generate_empty_file()
        (dummy, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutGood_')
        (dummy, self.outerr_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutErr_')

    def _generate_empty_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyIn_')
        fp = os.fdopen(fd,"w")
        fp.close()
        return fqfn

    def teardown_method(self, method):
        test_tools.temp_file_remover(self.empty_fqfn)
        test_tools.temp_file_remover(self.outgood_fqfn)
        test_tools.temp_file_remover(self.outerr_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestGristleValidator'))

    def test_empty_file(self):
        """ Should show proper handling of an empty file.
        """
        cmd = '%s %s --outgood %s --outerr %s -f 5' % (fq_pgm,
                                                       self.empty_fqfn,
                                                       self.outgood_fqfn,
                                                       self.outerr_fqfn)
        r = envoy.run(cmd)
        print r.std_out
        print r.std_err
        assert r.status_code == errno.ENODATA

        out_recs  = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0

        out_recs  = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0


    def test_empty_stdin(self):
        """ Should show proper handling of an empty file.
        """
        cmd = "cat %s | %s -d'|' -f 5 --outgood %s --outerr %s" % \
                (self.empty_fqfn, fq_pgm, self.outgood_fqfn, self.outerr_fqfn)
        r = envoy.run(cmd)
        print r.std_out
        print r.std_err
        assert r.status_code == errno.ENODATA

        out_recs  = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0

        out_recs  = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert len(out_recs) == 0



class TestSchemaValidation(object):

    def setup_method(self, method):

        self.pgm                   = fq_pgm
        self.std_7x7_fqfn, self.data_7x7  = test_tools.generate_7x7_test_file('TestGristleValidator7x7In_')
        (dummy, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_')
        (dummy, self.outerr_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_')
        self.schema_fqfn           = _generate_7x7_schema_file()

    def teardown_method(self, method):
        test_tools.temp_file_remover(self.std_7x7_fqfn)
        test_tools.temp_file_remover(self.outgood_fqfn)
        test_tools.temp_file_remover(self.outerr_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestGristleValidator'))


    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out     = response.std_out
        self.std_err     = response.std_err
        self.good_output = good_recs
        self.err_output  = err_recs


    def test_valid_schema_valid_data(self):

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --fieldcnt 7              \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --validschema %(schema)s  \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn,
                          'schema':  self.schema_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        print self.std_out
        print self.std_err
        print self.err_output

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 7
        assert len(self.std_out)     == 0
        # std_err should be 0, but coverage.py might write 46 bytes
        # to it:
        assert (len(self.std_err)    == 0
                or (len(self.std_err) < 50
                    and 'Coverage.py' in self.std_err))



class TestValidatingTheValidator(object):

    def setup_method(self, method):

        self.pgm                   = fq_pgm
        (dummy, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_')
        (dummy, self.outerr_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_')


    def test_baseline(self):
        self.in_fqfn     = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        schema           = _generate_foobarbatz_schema()
        self.schema_fqfn = _write_schema_file('foobarbatz', schema)

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)
        #pp(self.err_output)

        assert self.status_code      == 0
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 10000

    def test_invalid_dg_type_dg_minimum_combo(self):
        self.in_fqfn     = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        schema           = _generate_foobarbatz_schema()
        for field in schema['items']:
            if 'dg_type' in field:
                del field['dg_type']
        self.schema_fqfn = _write_schema_file('foobarbatz', schema)

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        # check for error msg, don't want tight coupling on something so likely
        # to change, so we'll just check for keywords
        assert self.std_out.startswith('Error')
        assert 'dg_type' in self.std_out

        assert self.status_code      == 1
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 0

    def test_invalid_dg_type(self):
        self.in_fqfn     = _generate_foobarbatz_file(10000)  # create a big file with 10,000 recs
        schema           = _generate_foobarbatz_schema()
        for field in schema['items']:
            if 'dg_type' in field:
                field['dg_type'] = 'string'
        self.schema_fqfn = _write_schema_file('foobarbatz', schema)

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print self.cmd
        r = envoy.run(self.cmd)
        self.get_outputs(r)

        # check for error msg, don't want tight coupling on something so likely
        # to change, so we'll just check for keywords
        assert self.std_out.startswith('Error')
        assert 'dg_type' in self.std_out

        assert self.status_code      == 1
        assert len(self.err_output)  == 0
        assert len(self.good_output) == 0


    def teardown_method(self, method):
        test_tools.temp_file_remover(self.in_fqfn)
        test_tools.temp_file_remover(self.schema_fqfn)
        test_tools.temp_file_remover(self.outgood_fqfn)
        test_tools.temp_file_remover(self.outerr_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestGristleValidator'))

    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out     = response.std_out
        self.std_err     = response.std_err
        self.good_output = good_recs
        self.err_output  = err_recs


class TestCSVDialects(object):

    def setup_method(self, method):

        self.pgm                    = fq_pgm
        (dummy, self.outgood_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidator3x3OutGood_')
        (dummy, self.outerr_fqfn)   = tempfile.mkstemp(prefix='TestGristleValidator3x3OutErr_')
        (dummy, self.outgood2_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator3x3OutGood2_')
        (dummy, self.outerr2_fqfn)  = tempfile.mkstemp(prefix='TestGristleValidator3x3OutErr2_')

    def teardown_method(self, method):
        ###don't want to delete these - they're external files:
        ###test_tools.temp_file_remover(self.in_fqfn)
        ###test_tools.temp_file_remover(self.schema_fqfn)
        test_tools.temp_file_remover(self.outgood_fqfn)
        test_tools.temp_file_remover(self.outerr_fqfn)
        test_tools.temp_file_remover(self.outgood2_fqfn)
        test_tools.temp_file_remover(self.outerr2_fqfn)
        test_tools.temp_file_remover(os.path.join(tempfile.gettempdir(), 'TestGristleValidator'))

    def get_outputs(self, response):
        print response.status_code
        print response.std_out
        print response.std_err

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        return response.status_code, response.std_out, response.std_err, good_recs, err_recs



    def test_quoted_csv(self):
        # create a big file with 10,000 recs
        self.in_fqfn     = _generate_foobarbatz_file(100, delimiter=True)
        schema           = _generate_foobarbatz_schema()
        self.schema_fqfn = _write_schema_file('foobarbatz', schema)

        self.cmd = """%(pgm)s %(in_fqfn)s          \
                         -d '|'                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        r = envoy.run(self.cmd)
        status_code, stdout, stderr, good_recs, err_recs = self.get_outputs(r)

        assert status_code    == 0
        assert len(err_recs)  == 0
        assert len(good_recs) == 100



    def test_header_vs_nonheader(self):
        """Tests how program handles files with or without headers
           and with hasheader or hasnoheader args.
        """
        self.in_fqfn     = os.path.join(data_dir, '3x3.csv')
        self.schema_fqfn = os.path.join(data_dir, '3x3_schema.yml')

        #---- noheader in file - no header arg - should figure it out
        self.cmd1 = """%(pgm)s %(in_fqfn)s         \
                         -d ','                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        r = envoy.run(self.cmd1)
        status1, stdout1, stderr1, good_recs1, err_recs1 = self.get_outputs(r)

        assert status1          == 0
        assert len(err_recs1)   == 0
        assert len(good_recs1)  == 3

        #---- noheader in file - hasnoheader arg 
        self.cmd2 = """%(pgm)s %(in_fqfn)s         \
                         -d ','                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --hasnoheader             \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        r = envoy.run(self.cmd2)
        status2, stdout2, stderr2, good_recs2, err_recs2 = self.get_outputs(r)

        assert status2          == 0
        assert len(err_recs2)   == 0
        assert len(good_recs2)  == 3


        #---- header in file - header arg 
        self.in_fqfn     = os.path.join(data_dir, '3x3_header.csv')
        self.cmd3 = """%(pgm)s %(in_fqfn)s         \
                         -d ','                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         --hasheader               \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        r = envoy.run(self.cmd3)
        status3, stdout3, stderr3, good_recs3, err_recs3 = self.get_outputs(r)

        assert status3          == 0
        assert len(err_recs3)   == 0
        assert len(good_recs3)  == 4

        assert len(good_recs1) == len(good_recs2)  == len(good_recs3) - 1
        assert len(err_recs1)  == len(err_recs2)   == len(err_recs3)
        assert status1         == status2          == status3


        #---- header in file - no header arg - should figure it out ---
        self.in_fqfn     = os.path.join(data_dir, '3x3_header.csv')
        self.cmd4 = """%(pgm)s %(in_fqfn)s         \
                         -d ','                    \
                         --validschema %(schema)s  \
                         --quoting 'quote_none'    \
                         --outgood %(outgood)s     \
                         --outerr  %(outerr)s      \
                         -s                        \
                   """ % {'pgm':     self.pgm,
                          'outgood': self.outgood_fqfn,
                          'outerr':  self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        r = envoy.run(self.cmd4)
        status4, stdout4, stderr4, good_recs4, err_recs4 = self.get_outputs(r)

        assert status4          == 0
        assert len(err_recs4)   == 0
        assert len(good_recs4)  == 4

        assert len(good_recs3) == len(good_recs4)
        assert len(err_recs3)  == len(err_recs4)
        assert status3         == status4
























