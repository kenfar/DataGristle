from os.path import basename, exists, join as pjoin
from pprint import pprint as pp
import sys
from typing import Any, Optional, Dict, List, Tuple, Union

import jsonschema
import ruamel.yaml as yaml

import datagristle.common as comm
import datagristle.csvhelper as csvhelper
import datagristle.file_io as file_io



class RecordProcessor:


    def __init__(self,
                 input_handler: file_io.InputHandler,
                 outfile_handler: file_io.OutputHandler,
                 outerr_handler: file_io.OutputHandler,
                 rec_validator: 'RecValidator',
                 err_out_fields: bool,
                 err_out_text: bool,
                 verbosity: int) -> None:

        self.input_handler = input_handler
        self.outfile_handler = outfile_handler
        self.outerr_handler = outerr_handler
        self.rec_validator = rec_validator
        self.err_out_fields = err_out_fields
        self.err_out_text = err_out_text
        self.verbosity = verbosity

        self.valid_rec_cnt = 0
        self.invalid_rec_cnt = 0
        self.invalid_field_cnt = 0

        # Set up fields for cleaning msgs when using err_out_fields or err_out_text:
        if self.outerr_handler.dialect.doublequote or self.outerr_handler.dialect.escapechar:
            self.outerr_escaping = True
        else:
            self.outerr_escaping = False
        self.outerr_delimiter = self.outerr_handler.dialect.delimiter
        self.outerr_alt_delimiter = ';' if self.outerr_delimiter == ',' else ','
        if csvhelper.get_quote_name(self.outerr_handler.dialect.quoting) == 'QUOTE_NONE':
            self.outerr_quotechar = None
            self.outerr_alt_quotechar = None
        else:
            self.outerr_quotechar = '"'
            self.outerr_alt_quotechar = "'" if self.outerr_quotechar == '"' else '"'


    def process_recs(self):

        for rec in self.input_handler:
            self._process_rec(rec)

        if self.verbosity in ('high', 'debug'):
            write_stats(self.input_handler.rec_cnt,
                        self.valid_rec_cnt,
                        self.invalid_rec_cnt)


    def _process_rec(self,
                     rec):

        write_appended_error_info = True
        write_field_error_recs = True

        if self.input_handler.dialect.has_header and self.input_handler.rec_cnt == 1:
            self.rec_validator.check_field_cnt(len(self.input_handler.header))
            if self.rec_validator.rec_error_count:
                self._write_error_rec(self.input_handler.header)
            else:
                self._write_valid_rec(self.input_handler.header)

        self.rec_validator.run_all_checks(rec)

        # Write recs:
        if self.rec_validator.rec_error_count:
            self._write_error_rec(rec)
        else:
            self._write_valid_rec(rec)


    def _write_valid_rec(self, rec):
        self.valid_rec_cnt += 1
        self.outfile_handler.write_rec(rec)


    def _write_error_rec(self,
                         rec):
        self.invalid_rec_cnt += 1
        self.invalid_field_cnt += self.rec_validator.rec_error_count
        if self.err_out_fields:
            rec.append('error_cnt=' + str(self.invalid_field_cnt))
            rec.append('col_num=' + self.rec_validator.get_error_column())
            rec.append('validator=' + self.rec_validator.get_error_validator())
            rec.append('msg=' + self.rec_validator.get_error_msg())
        self.outerr_handler.write_rec(rec)
        if self.err_out_text:
            for error_num, error in enumerate(self.rec_validator.rec_errors):
                try:
                    field_num = self.rec_validator.rec_errors[error_num]['error.path'][0]
                    field_name = self.rec_validator.header.get_field_name(field_num)
                    field_title = self.rec_validator.get_column_title(field_num)

                    self._clean_writer(f"    column: position={field_num}; header-name={field_name}; schema-title={field_title}")
                    self._clean_writer(f"       validator: {self.rec_validator.get_error_validator(error_num)}")
                    self._clean_writer(f"       msg: {self.rec_validator.get_error_msg(error_num, 80)}")
                except IndexError:  # the following is for a field_cnt error:
                    self._clean_writer("    column: unknown")
                    self._clean_writer(f"       validator: {self.rec_validator.get_error_validator(error_num)}")
                    self._clean_writer(f"       msg: {self.rec_validator.get_error_msg(error_num, 80)}")


    def _clean_writer(self,
                     string:str) -> None:
        """ 'cleans' messages to be written to the outerr_handler

        This will replace any delimiters or quote chars in the message so that it doesn't
        conflict with the csv dialect - but only if no escapechar or double-quoting was provided.
        We're doing this because otherwise users would have to specify
        """
        if self.outerr_escaping:
            clean_string = string
        else:
            clean_string = string.replace(self.outerr_delimiter, self.outerr_alt_delimiter)
            if self.outerr_quotechar:
                clean_string = string.replace(self.outerr_quotechar, self.outerr_alt_quotechar)

        self.outerr_handler.write_rec([clean_string])



def write_stats(input_cnt: int, valid_cnt: int, invalid_cnt: int) -> None:
    """ Writes input, output, and validation counts to stdout.
    """
    print('')
    print('input_cnt        | %d ' % input_cnt)
    print('invalid_cnt      | %d ' % invalid_cnt)
    print('valid_cnt        | %d ' % valid_cnt)



def load_schema(schema_file: str,
                schema_path: List[str]) -> Optional[Dict[Any, Any]]:
    """ Loads validation schema.
        If the schema_file argument is None, then it will not load,
        this is useful when the user wants to check field counts,
        but does not have or want to use a validation schema.
    """
    def find_schema_file_on_path(schema_file):
        if exists(schema_file):
            return schema_file
        elif basename(schema_file) == schema_file:
            for schema_dir in schema_path:
                temp_schema_file = pjoin(schema_dir, schema_file)
                if exists(temp_schema_file):
                    return temp_schema_file
            else:
                comm.abort('Error: schema file not found',
                           f'File not found: {schema_file}')

    schema_dict = None
    if schema_file:
        schema_file = find_schema_file_on_path(schema_file)
        with open(schema_file, 'r') as schema_buf:
            schema_dict = yaml.safe_load(schema_buf)

        try:
            config_validation_simple(schema_dict)
        except ValueError as err:
            comm.abort('Error: invalid validation schema', err)

        try:
            config_validation_detailed(schema_dict)
        except jsonschema.exceptions.SchemaError as err:
            comm.abort('Error: invalid validation schema', err)

    return schema_dict




class RecValidator(object):
    # how to provide caller with actual vs valid values?

    def __init__(self,
                 header: csvhelper.Header,
                 valid_field_cnt: Optional[int] = None,
                 rec_schema=None) -> None:

        self.header = header
        self.rec_schema = rec_schema
        self.valid_field_cnt: Optional[int] = valid_field_cnt
        self.last_field_cnt: Optional[int] = None
        self.rec_errors: List[dict[str, str]] = []
        self.rec_error_count = 0
        if rec_schema:
            self.validator = jsonschema.Draft7Validator(self.rec_schema)
        else:
            self.validator = None


    def run_all_checks(self,
                       record: List[str]):

        self.rec_errors = []
        self.rec_error_count = 0

        self.check_field_cnt(len(record))
        if self.rec_schema and self.rec_error_count == 0:
            self.check_schema(record)


    def check_field_cnt(self,
                        actual_field_cnt: int):
        """ If no valid_field_cnt was assigned originally, set it to the first
            actual field cnt.
        """
        if self.valid_field_cnt is None:
            self.valid_field_cnt = actual_field_cnt
        self.last_field_cnt = actual_field_cnt

        if actual_field_cnt != self.valid_field_cnt:
            self.rec_errors.append({'error.message': 'bad field count - should be %d but is: %d'  % \
                                                  (self.valid_field_cnt, self.last_field_cnt),
                                    'error.path': '',
                                    'error.validator': 'field_cnt'})
            self.rec_error_count += 1


    def check_schema(self,
                     record: List[str]):
        """ First translates the csv string to appropriate types.
            Then run the jsonschema validation.
        """
        typed_record = self.fix_types(record, self.rec_schema)
        errors = self.validator.iter_errors(typed_record)
        for error in errors:
            self.rec_errors.append({'error.message': error.message,
                                    'error.path': error.path,
                                    'error.validator': error.validator})
            self.rec_error_count += 1


    @staticmethod
    def fix_types(record, schema):
        new_record = []
        for i,field in enumerate(record):
            try:
                schema_field_type = schema['items'][i].get('type')
            except IndexError:
                comm.abort('Error: schema does not have entries for all fields',
                           f'field number {i} not found in schema')
            if schema_field_type == 'integer':
                try:
                    new_field = int(field)
                except ValueError:
                    new_field = field
            elif schema_field_type == 'number':
                try:
                    new_field = float(field)
                except ValueError:
                    new_field = field
            else:
                try:
                    new_field = field
                except ValueError:
                    new_field = field
            new_record.append(new_field)
        return new_record


    def get_column_title(self, col_number) -> str:
        return self.rec_schema['items'][col_number].get('title', '')


    def get_error_column(self,
                         error_num=0):
        try:
            col = str(self.rec_errors[error_num]['error.path'][0])
        except IndexError:
            col = ''
        return col


    def get_error_validator(self,
                            error_num=0):
        return self.rec_errors[error_num]['error.validator']


    def get_error_msg(self,
                      error_num=0,
                      limit=None):
        if limit:
            msg = str(self.rec_errors[error_num]['error.message'])
            if len(msg) > limit:
                msg = msg[:limit] + '...'
            return msg
        else:
            return str(self.rec_errors[error_num]['error.message'])



def config_validation_simple(schema: Dict[Any, Any]):

    valid_keys = ['type', 'minimum', 'maximum', 'minLength', 'maxLength', 'title',
                  'description', 'enum', 'pattern', 'blank']

    def validate_schema():
        """ Validates entire schema - with a few high-level checks, and by
            running _validate_field_checks for each field validation set.
        """
        if 'items' not in schema:
            comm.abort("Error: invalid schema, missing 'items' key")
        if len(schema.keys()) != 1:
            comm.abort("Error: invalid schema, incorrect number of 'items' keys")

        for field_checks in schema['items']:
            for v_key in field_checks.keys():
                validate_field_checks(v_key, field_checks[v_key])

    def validate_field_checks(key: str,
                              value: Union[str, bool]) -> None:
        """ Validate individual field checks:
                - ensure all keys are valid & supported
                - ensure values are valid for the keys
        """
        if key not in valid_keys:
            comm.abort('Error:  invalid schema, unsupported key value: %s' % key)

        if key == 'blank':
            if value not in [True, False]:
                comm.abort('Error:  invalid schema, unknown value for blank: %s' % value)

        if key == 'type':
            if value not in ['string', 'number', 'boolean', 'null']:
                comm.abort(f'Error: invalid schema, improper type of {value}')

    validate_schema()



def config_validation_detailed(schema):
    """ Run a very detailed verification of the confg.

    We don't depend on this one alone since the resulting error messages
    are very difficult to read.
    """

    try:
        jsonschema.validate(instance=None, schema=schema)
    except jsonschema.exceptions.SchemaError as err:
        msgs = ['See jsonschema docs for help: https://json-schema.org/understanding-json-schema/']
        for msg in err.context:
            msgs.append(repr(msg))
        msg_str = '\n'.join(msgs)
        comm.abort('Error: schema is invalid',
                    msg_str)

                   #'See jsonschema docs for help: https://json-schema.org/understanding-json-schema/',
