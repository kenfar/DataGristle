#!/usr/bin/env python

from dataclasses import dataclass
import errno
from operator import itemgetter
from os.path import isfile, isdir
from os.path import dirname, basename
from os.path import join  as pjoin
from pprint import pprint as pp
import subprocess
import sys
import time
from typing import List, Dict, Any, Union, Tuple, Optional

import datagristle.common as comm
import datagristle.csvhelper as csvhelper
import datagristle.file_io as file_io


class SortKeysConfig(object):

    def __init__(self,
                 sort_keys: List[str]):

        self.key_fields: List[SortKeyRecord] = []
        self.load_config(sort_keys)


    def load_config(self,
                    sort_keys: List[str]) -> None:

        for key_field in sort_keys:
            sort_key_rec = SortKeyRecord(key_field)
            self.key_fields.append(sort_key_rec)


    def multi_string_orders(self) -> bool:
        string_orders = set([x.order for x in self.key_fields if x.type == 'str'])
        return bool(len(string_orders) > 1)


    def get_primary_order(self) -> str:
        """Returns:
             - A string - either 'forward' or 'reverse'
        """
        string_order = list(set([x.order for x in self.key_fields if x.type == 'str']))
        if string_order:
            return string_order[0]
        else:
            return self.key_fields[0].order # yep, returning any ole arbitrary type

    def get_sort_fields(self) -> List[int]:
        """ Get the list of columns to sort the self.keys list on
            This will always be a sequential list of numbers starting with 0.
        """
        return list(range(len(self.key_fields)))



@dataclass
class SortKeyRecord:
    position: int
    type: str
    order: str

    def __init__(self,
                 key_field: str) -> None:
        self.order_transform = {'f':'forward',
                                'r':'reverse'}
        self.type_transform = {'s':'str',
                               'i':'int',
                               'f':'float'}
        self.load_from_string(key_field)


    def load_from_string(self,
                         key_field: str) -> None:
        """ The input string looks like this: '5SF 3ir 2ff'
        """
        if len(key_field) < 3:
            raise ValueError(f'Invalid key field value: {key_field} - expect 3+ characters')

        try:
            self.order = self.order_transform[key_field[-1].lower()]
        except KeyError:
            raise ValueError(f"Invalid key order value - should be forward or reverse ")

        try:
            self.type = self.type_transform[key_field[-2].lower()]
        except KeyError:
            raise ValueError(f"Invalid key type value - should be str, int or float ")

        try:
            self.position = int(key_field[:-2])
        except ValueError:
            raise ValueError(f"Invalid key position value - should be an integer")




class CSVPythonSorter(object):
    """
    """

    def __init__(self,
                 in_fqfn: str,
                 out_fqfn: str,
                 sort_keys_config: SortKeysConfig,
                 dialect: csvhelper.Dialect,
                 dedupe: bool,
                 keep_header: bool = True) -> None:

        self.dedupe = dedupe
        self.sort_key_config = sort_keys_config
        self.keep_header = keep_header

        self.all_recs: List[str] = []
        self.keys: List[Tuple[Any, ...]] = []
        self.header_rec = None

        self.stats = {}
        self.stats['recs_deduped'] = 0

        #todo: handle relative path subtleties:
        #    for reference:  https://stackoverflow.com/questions/918154/relative-paths-in-python
        #if not isdir(dirname(out_fqfn)):
        #    raise ValueError('Invalid sort output directory: %s' % out_fqfn)

        self.input_handler = file_io.InputHandler([in_fqfn], dialect)

        self.output_handler = file_io.OutputHandler(out_fqfn,
                                                    self.input_handler.dialect,
                                                    sys.stdout)


    def sort_file(self):
        """ Sort input file giving output file
            Returns a dictionary of counts.
        """
        self._load_file_and_prepare_data()

        if self.sort_key_config.multi_string_orders():
            self._multipass_sort()
        else:
            self._singlepass_sort()

        self._write_file_and_dedupe()

        self.stats['recs_read'] = self.input_handler.rec_cnt
        self.stats['recs_written'] = self.output_handler.rec_cnt


    def close(self) -> int:
        self.input_handler.close()
        self.output_handler.close()

        if self.input_handler.rec_cnt == 0:  # catches empty stdin
            return errno.ENODATA  # is a 61 on linux
        else:
            return 0


    def _load_file_and_prepare_data(self) -> None:
        #print('\n ------------------ Read Phase: -------------------------')
        start_time = time.time()
        keys = self.keys
        all_recs = self.all_recs
        primary_order = self.sort_key_config.get_primary_order()
        if self.input_handler.dialect.has_header:
            has_header_adjustment = 1
        else:
            has_header_adjustment = 0

        for rec in self.input_handler:
            if self.input_handler.dialect.has_header and self.input_handler.rec_cnt == 1:
                self.header_rec = rec
            else:
                all_recs.append(rec)
                sort_values = self._get_sort_values(self.sort_key_config.key_fields, rec, primary_order)
                keys.append((*sort_values, self.input_handler.rec_cnt - 1 - has_header_adjustment))
        #print(f'    duration = {(time.time() - start_time):.4f}')


    def _get_sort_values(self,
                         key_fields: List[Any],
                         rec: List[Union[str, int, float]],
                         primary_order: str) -> List[Any]:

        try:
            sort_values = [transform(rec[key_field.position], key_field, primary_order) for key_field in key_fields]
        except IndexError:
            comm.abort('Error: key references columns that does not exist in record', f'{rec=}')
        return sort_values


    def _singlepass_sort(self) -> None:
        """ Sorts the keys in a single direction
        """
        #print('\n ------------------ Sort Phase: -------------------------')
        start_time = time.time()
        sort_fields = self.sort_key_config.get_sort_fields()
        primary_order = self.sort_key_config.get_primary_order()
        if primary_order == 'forward':
            self.keys.sort(key=itemgetter(*sort_fields))
        else:
            self.keys.sort(key=itemgetter(*sort_fields), reverse=True)
        #print(f'    duration = {(time.time() - start_time):.6f}')


    def _multipass_sort(self) -> None:
        """ Sorts keys in multiple directions
        """
        #print('\n ------------------ Multi-Pass Sort Phase: -------------------------')
        start_time = time.time()

        sort_fields = self.sort_key_config.get_sort_fields()
        for i, key_field in enumerate(reversed(self.sort_key_config.key_fields)):
            sort_field = sort_fields[len(sort_fields) - (i+1)]
            if key_field.order == 'reverse':
                self.keys.sort(key=itemgetter(sort_field), reverse=True)
            else:
                self.keys.sort(key=itemgetter(sort_field))
        #print(f'    duration = {(time.time() - start_time):.6f}')


    def _write_file_and_dedupe(self) -> None:
        #note: it is no longer writing the header record out
        #print('\n ------------------ Write Phase: -------------------------')
        keys = self.keys
        all_recs = self.all_recs
        stats = self.stats

        start_time = time.time()

        # Run it once to initiate - especially for unit testing.
        isduplicate(None)

        if self.keep_header and self.header_rec:
            self.output_handler.write_rec(self.header_rec)

        for key in keys:
            if self.dedupe and isduplicate(key=key[:-1]):
                stats['recs_deduped'] += 1
            else:
                self.output_handler.write_rec(all_recs[key[-1]])
        #print(f'    duration = {(time.time() - start_time):.6f}')



def isduplicate(key: Tuple[Any, ...],
                last_key: Optional[List[Any]] = [None]) -> bool:

    if last_key[0] is not None and last_key[0] == key:
        return True
    else:
        last_key.clear()
        last_key.append(key)
        return False



def transform(field_value: str,
              key_field: SortKeyRecord,
              primary_order: str) -> Union[str, int, float]:

    transformed_field_value: Union[str, int, float] = None
    if key_field.type == 'str':
        transformed_field_value = field_value
    elif key_field.type == 'int':
        transformed_field_value = int(field_value)
    elif key_field.type == 'float':
        transformed_field_value = float(field_value)
    else:
        raise ValueError(f'Invalid key-field type: {key_field.type}')

    if (primary_order == 'forward'
            and key_field.type in ('int', 'float')
            and key_field.order == 'reverse'):
        return transformed_field_value * -1
    else:
        return transformed_field_value



class CSVSorter(object):
    """ Sort a file.

    Args:
        dialect:  a csv module dialect
        key_fields_0off: a list of fields to sort the file with - identified by
                 an numeric value representing the position of the field, given a zero-offset.
        tmp_dir: a directory to use for sort temp space.  Defaults to None, in
                 which case the input file directory will be used.
        out_dir: a directory to use for the output file.  Defaults to None, in
                 which case the input file directory will be used.
    Raises:
        ValueError: if tmp_dir or out_dir are provided but do not exist
        ValueError: if sort keys are invalid
        IOError: if unix sort fails
    """

    def __init__(self,
                 dialect: csvhelper.Dialect,
                 key_fields_0off: List[int],
                 tmp_dir: str = None,
                 out_dir: str = None) -> None:

        assert dialect          is not None
        assert key_fields_0off  is not None

        self.dialect = dialect

        if tmp_dir and not isdir(tmp_dir):
            raise ValueError('Invalid sort temp directory: %s' % tmp_dir)
        else:
            self.tmp_dir = tmp_dir

        if out_dir and not isdir(out_dir):
            raise ValueError('Invalid sort output directory: %s' % out_dir)
        else:
            self.out_dir = out_dir

        # convert from std datagristle 0offset to sort's 1offset
        try:
            key_fields_1off = [int(x)+1 for x in key_fields_0off]
        except ValueError:
            print('Error: invalid non-numeric sort key: %s' % key_fields_0off)
            raise

        self.field_opt = ''
        self.field_key_1off = []
        for field in key_fields_1off:
            self.field_opt += ' -k %s' % field
            self.field_key_1off.append(field)


    def sort_file(self, in_fqfn: str, out_fqfn: str = None) -> str:
        """ Sort input file giving output file.

        Args:
            in_fn:  input file name
            out_fn: output file name.  Defaults to None.  If it is None
                    then the name will be derrived from input file + .sorted
        Returns:
            out_fqfn: the fully-qualified output file name
        Raises:
            IOError: if the sort produces a non-zero return code
            ValueError: if the input file is invalid

        Notes:
           - that sort_file does not have very sophisticated csv-sorting
             features: it doesn't recognize quoting or escaping, so control
             characters in the data can throw off the record structure.
           - there may be slight differences in this behavior
             between linux and mac.
           - fields are not sorted numerically - which does not matter since
             data just must be in the same order for both versions of the
             same file.
        """

        if not out_fqfn:
            out_dir = self.out_dir or dirname(in_fqfn)
            out_fqfn = pjoin(out_dir, basename(in_fqfn) + '.sorted')

        if not isfile(in_fqfn):
            raise ValueError('Invalid input file: %s' % in_fqfn)

        cmd = ['sort']
        for field in self.field_key_1off:
            cmd.append('-k')
            cmd.append(str(field) + ',' + str(field))
        cmd.append('--field-separator')
        cmd.append(self.dialect.delimiter)
        cmd.append('-T')
        cmd.append(self.tmp_dir)
        cmd.append(in_fqfn)
        cmd.append('-o')
        cmd.append(out_fqfn)

        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                close_fds=True)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            raise IOError(f'invalid sort return code: {proc.returncode}, {repr(stdout)}, {repr(stderr)}')

        return out_fqfn


    @staticmethod
    def _get_sort_del(self, delimiter: str) -> str:
        """ Gets a quoted, sort-acceptable delimiter given a regular delimiter.
            Was necessary when passing tabs as delimiters through the shell.
        """
        if delimiter == '\t':
            return "$'\t'" # used for envoy
            #alternative, got stuck on envoy i think:
            #return ''' " `echo '\t'` " '''
        else:
            return "'%s'" % delimiter  # good for envoy, not subprocess

