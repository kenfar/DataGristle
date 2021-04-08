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
#pylint: disable=empty-docstring

import errno
import fileinput
import os
import shutil
import tempfile
from os.path import join as pjoin, dirname

import envoy
import ruamel.yaml as yaml

import datagristle.test_tools as test_tools

script_dir = dirname(os.path.dirname(os.path.realpath((__file__))))
fq_pgm = pjoin(script_dir, 'gristle_validator')




def _generate_foobarbatz_file(recs, dir_name, quoting='quote_none'):
    (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorIn_', dir=dir_name)
    fp = os.fdopen(fd,"w")
    for rec in range(recs):
        if quoting == 'quote_all':
            rec = '"foo","bar","batz","1.9","2","%d"' % rec
        elif quoting == 'quote_nonnumeric':
            rec = '"foo","bar","batz",1.9,2,%d' % rec
        elif quoting == 'quote_none':
            rec = 'foo,bar,batz,1.9,2,%d' % rec
        else:
            raise ValueError("Invalid quoting: %s" % quoting)
        fp.write('%s\n' % rec)
    fp.close()
    return fqfn


def _generate_foobarbatz_schema():
    schema = {'items': []}
    field0 = {'title':     'foo',
              'blank':     False,
              'minLength': 3,
              'maxLength': 3,
              'required':  True,
              'enum':      ['foo']}
    schema['items'].append(field0)
    field1 = {'title':     'bar',
              'blank':     False,
              'minLength': 3,
              'maxLength': 3,
              'required':  True}
    schema['items'].append(field1)
    field2 = {'title':     'batz',
              'blank':     False,
              'minLength': 4,
              'maxLength': 4,
              'required':  True}
    schema['items'].append(field2)
    field3 = {'title':     'field3',
              'blank':     False,
              'required':  True,
              'dg_type':   'float',
              'dg_minimum': 1,
              'dg_maximum': 2}
    schema['items'].append(field3)
    field4 = {'title':     'field4',
              'blank':     False,
              'required':  True,
              'dg_type':   'integer',
              'dg_minimum': 1,
              'dg_maximum': 99}
    schema['items'].append(field4)
    field5 = {'title':     'rowcnt',
              'blank':     False,
              'required':  True,
              'dg_type':   'integer',
              'dg_minimum': '0',
              'dg_maximum': 9999999}
    schema['items'].append(field5)
    return schema


def _write_schema_file(name, schema, dir_name):
    temp_fqfn = pjoin(dir_name, 'test_gristle_validator_%s_schema.yml' % name)
    with open(temp_fqfn, 'w') as schema_file:
        schema_file.write(yaml.dump(schema))
    return temp_fqfn



def _generate_7x7_schema_file(dir_name):
    schema = {'items': []}
    col0 = {'title':     'col0',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col0)
    col1 = {'title':     'col1',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col1)
    col2 = {'title':     'col2',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col2)
    col3 = {'title':     'col3',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col3)
    col4 = {'title':     'col4',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col4)
    col5 = {'title':     'col5',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col5)
    col6 = {'title':     'col6',
            'blank':     False,
            'minLength': 3,
            'maxLength': 3,
            'required':  True,
            'pattern':   r'\b\d-\d'}
    schema['items'].append(col6)

    return _write_schema_file('7x7', schema, dir_name)




class TestFieldCount(object):
    """ Tests gristle_validator functionality involved in verifying
        that all records within a file have the correct number of fields.
    """


    def setup_method(self, method):

        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.pgm = fq_pgm
        self.std_7x7_fqfn, self.data_7x7 = test_tools.generate_7x7_test_file('TestGristleValidator7x7In_',
                                                                             delimiter=',', dirname=self.tmp_dir)
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_', dir=self.tmp_dir)

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def get_outputs(self, response):
        print(response.status_code)
        print(response.std_out)
        print(response.std_err)

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out = response.std_out
        self.std_err = response.std_err
        self.good_output = good_recs
        self.err_output = err_recs



    def test_good_field_cnt(self):

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --quoting 'quote_none'
                         --field-cnt 7
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                   """ % {'pgm': self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print('\n command: %s' % self.cmd)

        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert len(self.good_output) == 7
        assert self.good_output == self.data_7x7


    def test_field_cnt_default(self):
        """ Test running without a field_cnt
        """

        self.cmd = """%(pgm)s                      \
                         --infiles %(in_fqfn)s     \
                         -d ','                    \
                         --quoting 'quote_none'    \
                         --outfile %(outfile)s     \
                         --errfile %(errfile)s     \
                   """ % {'pgm': self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert self.good_output == self.data_7x7


    def test_bad_field_cnt(self):

        self.cmd = """%(pgm)s                      \
                         --infiles %(in_fqfn)s     \
                         -d ','                    \
                         --field-cnt 70             \
                         --quoting 'quote_none'    \
                         --outfile %(outfile)s     \
                         --errfile %(errfile)s      \
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == errno.EBADMSG
        assert len(self.err_output) == 7
        assert not self.good_output

        orig_recs = []
        for rec in self.err_output:
            fields = rec.split(',')
            assert len(fields) == 8  # extra field for msg
            orig_recs.append(','.join(fields[:7]))
        assert orig_recs == self.data_7x7



    def test_stats_option(self):
        """ The stats option will create a report to stdout
            The stats should look like this:
                input_cnt        | 7
                invalid_cnt      | 7
                valid_cnt        | 0
        """
        self.cmd = """%(pgm)s                      \
                         --infiles %(in_fqfn)s     \
                         -d ','                    \
                         --field-cnt 70             \
                         --quoting 'quote_none'    \
                         --outfile %(outfile)s     \
                         --errfile  %(errfile)s    \
                         --verbosity high          \
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == errno.EBADMSG
        assert self.err_output
        assert not self.good_output
        assert self.std_out
        assert self.std_out
        # std_err should be 0, but coverage.py might write 46 bytes to it:
        assert not self.std_err or (len(self.std_err) < 50 and 'Coverage.py' in self.std_err)

        std_out_recs = self.std_out.split('\n')
        input_cnt_found = False
        invalid_cnt_found = False
        valid_cnt_found = False

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


    def test_random_out_1(self):
        in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 1.0
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert len(self.good_output) == 10000


    def test_random_out_0(self):
        in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 0
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert not self.good_output


    def test_random_out_01(self):

        in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --random-out 0.1
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': in_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)

        assert self.status_code == 0
        assert not self.err_output
        assert (0.2 * 100000) > len(self.good_output) > (0.05 * 10000)



class TestEmptyFile(object):

    def setup_method(self, method):
        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.empty_fqfn = self._generate_empty_file()
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyOutErr_', dir=self.tmp_dir)

    def _generate_empty_file(self):
        (fd, fqfn) = tempfile.mkstemp(prefix='TestGristleValidatorEmptyIn_', dir=self.tmp_dir)
        fp = os.fdopen(fd, "w")
        fp.close()
        return fqfn

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def test_empty_file(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f'''{fq_pgm} \
                  --infiles {self.empty_fqfn} \
                  --outfile {self.outgood_fqfn} \
                  --errfile {self.outerr_fqfn} \
                  -f 5
                  -d ','
                  -q quote_none
               '''
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == errno.ENODATA

        out_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

        out_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs


    def test_empty_stdin(self):
        """ Should show proper handling of an empty file.
        """
        cmd = f"""cat {self.empty_fqfn} | {fq_pgm} -d',' -f 5
                        --outfile {self.outgood_fqfn}
                        --errfile {self.outerr_fqfn}
                        -d ','
                        -q quote_none
                        --has-no-header
               """
        runner = envoy.run(cmd)
        print(runner.std_out)
        print(runner.std_err)
        assert runner.status_code == errno.ENODATA

        out_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs

        out_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            out_recs.append(rec)
        fileinput.close()
        assert not out_recs



class TestSchemaValidation(object):

    def setup_method(self, method):

        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.pgm = fq_pgm
        self.std_7x7_fqfn, _ = test_tools.generate_7x7_test_file('test_7x7_in_',
                                                                 delimiter=',', dirname=self.tmp_dir)
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='test_7x7_out_good_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='test_7x7_out_drr_', dir=self.tmp_dir)
        self.schema_fqfn = _generate_7x7_schema_file(self.tmp_dir)

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def get_outputs(self, response):
        print(response.status_code)
        print(response.std_out)
        print(response.std_err)

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out = response.std_out
        self.std_err = response.std_err
        self.good_output = good_recs
        self.err_output = err_recs


    def test_valid_schema_valid_data(self):

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 7
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --valid-schema %(schema)s
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.std_7x7_fqfn,
                          'schema':  self.schema_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)
        print(self.err_output)

        assert self.status_code == 0
        assert not self.err_output
        assert len(self.good_output) == 7
        assert not self.std_out
        # std_err should be 0, but coverage.py might write 46 bytes to it:
        assert not self.std_err or (len(self.std_err) < 50 and 'Coverage.py' in self.std_err)


    def test_valid_schema_invalid_dgmin_and_dgmax(self):

        dlm = ','
        data_7x7 = []
        (fd, input_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7In_', dir=self.tmp_dir)
        with open(input_fqfn, 'w') as out:
            out.write('"foo","bar","batz","1.7","2","0"\n')
            out.write('"foo","bar","batz","0.7","3","1"\n')   # will be rejected for the value 0.7
            out.write('"foo","bar","batz","2.9","999","2"\n') # will be rejected for the value 2.9
        schema = _generate_foobarbatz_schema()
        schema_fqfn = _write_schema_file('foobarbatz', schema, dir_name=self.tmp_dir)

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --field-cnt 6
                         --quoting 'quote_all'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                         --valid-schema %(schema)s
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': input_fqfn,
                          'schema':  schema_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        print(self.std_out)
        print(self.std_err)
        print(self.err_output)

        assert self.status_code == 74
        assert len(self.err_output) == 2
        assert len(self.good_output) == 1
        assert not self.std_out
        # std_err should be 0, but coverage.py might write 46 bytes to it:
        assert not self.std_err or (len(self.std_err) < 50 and 'Coverage.py' in self.std_err)



class TestValidatingTheValidator(object):

    def setup_method(self, method):

        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.pgm = fq_pgm
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator7x7OutErr_', dir=self.tmp_dir)

    def teardown_method(self, method):
        shutil.rmtree(self.tmp_dir)

    def test_baseline(self):
        self.in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        schema = _generate_foobarbatz_schema()
        self.schema_fqfn = _write_schema_file('foobarbatz', schema, dir_name=self.tmp_dir)

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --valid-schema %(schema)s
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile %(errfile)s
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)
        #pp(self.err_output)

        assert self.status_code == 0
        assert not self.err_output
        assert len(self.good_output) == 10000

    def test_invalid_dg_type_dg_minimum_combo(self):
        self.in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        schema = _generate_foobarbatz_schema()
        for field in schema['items']:
            if 'dg_type' in field:
                del field['dg_type']
        self.schema_fqfn = _write_schema_file('foobarbatz', schema, dir_name=self.tmp_dir)

        self.cmd = """%(pgm)s                      \
                         --infiles %(in_fqfn)s     \
                         -d ','                    \
                         --valid-schema %(schema)s \
                         --quoting 'quote_none'    \
                         --outfile %(outfile)s     \
                         --errfile  %(errfile)s    \
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)

        # check for error msg, don't want tight coupling on something so likely
        # to change, so we'll just check for keywords
        assert self.std_out.startswith('Error')
        assert 'dg_type' in self.std_out

        assert self.status_code == 1
        assert not self.err_output
        assert not self.good_output

    def test_invalid_dg_type(self):
        self.in_fqfn = _generate_foobarbatz_file(10000, dir_name=self.tmp_dir)
        schema = _generate_foobarbatz_schema()
        for field in schema['items']:
            if 'dg_type' in field:
                field['dg_type'] = 'string'
        self.schema_fqfn = _write_schema_file('foobarbatz', schema, dir_name=self.tmp_dir)

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --valid-schema %(schema)s
                         --quoting 'quote_none'
                         --outfile %(outfile)s
                         --errfile  %(errfile)s
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        print(self.cmd)
        runner = envoy.run(self.cmd)
        self.get_outputs(runner)

        # check for error msg, don't want tight coupling on something so likely
        # to change, so we'll just check for keywords
        assert self.std_out.startswith('Error')
        assert 'dg_type' in self.std_out

        assert self.status_code == 1
        assert not self.err_output
        assert not self.good_output

    def get_outputs(self, response):
        print(response.status_code)
        print(response.std_out)
        print(response.std_err)

        good_recs = []
        for rec in fileinput.input(self.outgood_fqfn):
            good_recs.append(rec[:-1])
        fileinput.close()

        err_recs = []
        for rec in fileinput.input(self.outerr_fqfn):
            err_recs.append(rec[:-1])
        fileinput.close()

        self.status_code = response.status_code
        self.std_out = response.std_out
        self.std_err = response.std_err
        self.good_output = good_recs
        self.err_output = err_recs


class TestCSVDialects(object):

    def setup_method(self, method):

        self.tmp_dir = tempfile.mkdtemp(prefix='TestGristleValidator_')
        self.pgm = fq_pgm
        (_, self.outgood_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator3x3OutGood_', dir=self.tmp_dir)
        (_, self.outerr_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator3x3OutErr_', dir=self.tmp_dir)
        (_, self.outgood2_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator3x3OutGood2_', dir=self.tmp_dir)
        (_, self.outerr2_fqfn) = tempfile.mkstemp(prefix='TestGristleValidator3x3OutErr2_', dir=self.tmp_dir)

    def teardown_method(self, method):
        ###don't want to delete these - they're external files:
        ###test_tools.temp_file_remover(self.in_fqfn)
        ###test_tools.temp_file_remover(self.schema_fqfn)
        shutil.rmtree(self.tmp_dir)

    def get_outputs(self, response):
        print(response.status_code)
        print(response.std_out)
        print(response.std_err)

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
        self.in_fqfn = _generate_foobarbatz_file(100, dir_name=self.tmp_dir, quoting='quote_nonnumeric')
        schema = _generate_foobarbatz_schema()
        self.schema_fqfn = _write_schema_file('foobarbatz', schema, dir_name=self.tmp_dir)

        self.cmd = """%(pgm)s
                         --infiles %(in_fqfn)s
                         -d ','
                         --valid-schema %(schema)s
                         --quoting quote_nonnumeric
                         --outfile %(outfile)s
                         --errfile  %(errfile)s
                   """ % {'pgm':     self.pgm,
                          'outfile': self.outgood_fqfn,
                          'errfile': self.outerr_fqfn,
                          'in_fqfn': self.in_fqfn,
                          'schema':  self.schema_fqfn}
        runner = envoy.run(self.cmd)
        status_code, stdout, stderr, good_recs, err_recs = self.get_outputs(runner)
        os.system('cat %s' % self.in_fqfn)
        assert status_code == 0

