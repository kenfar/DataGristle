#!/usr/bin/env python

import csv
import json
from os.path import isfile
from os.path import basename
from os.path import join  as pjoin
from pprint import pprint as pp
from typing import Dict, Tuple, List, Union, Any, Optional, IO

import datagristle.common as comm
from datagristle.common import abort
import datagristle.csvhelper as csvhelper

OUTPUT_TYPES = ['insert', 'delete', 'same', 'chgnew', 'chgold']

FieldPositionsType = List[int]
RecordType = List[str]



class FileDelta:
    """" Compares two files based on a common key writing results to multiple
         output files.

    Args:
        out_dir: the output file directory
        dialect: a csv dialect object
    Raises:
        ValueError: if field_type is invalid
        ValueError: if the same field is referenced by ignore_fields and key_fields
    """

    def __init__(self,
                 out_dir: str,
                 dialect: csvhelper.Dialect) -> None:
        self.out_dir = out_dir
        self.dialect = dialect
        self.join_fields: FieldPositionsType = []
        self.compare_fields: FieldPositionsType = []
        self.ignore_fields: FieldPositionsType = []
        self.dry_run: bool = False
        self.old_rec: List[str] = None
        self.new_rec: List[str] = None

        self.new_read_cnt = 0
        self.old_read_cnt = 0
        self.out_file: Dict[str, IO[str]] = {}
        self.out_fqfn: Dict[str, str] = {}
        self.out_writer: Dict[str, Any] = {}
        self.out_counts: Dict[str, int] = {}
        self.dass = DeltaAssignments()

    def set_fields(self,
                   field_type: str,
                   *fields: Any) -> None:
        """ Assign fields to joins, compares and ignores lists.

        Args:
            field_type - must be 'join', 'compare' or 'ignore'
            *fields - the list of 0-offset field numbers.  Multiple
                      representations are accepted:
                      - string:          '0,1,3'
                      - list of numbers: 0,1,3
                      - list of strings: '0', '1', '3'
                      - single number:   0
                      - single string:   '0'
        Returns:
            nothing
        Raises
            ValueError: if field_type is invalid
        """
        if len(fields) == 1 and ',' in str(fields[0]):
            split_fields = fields[0].split(',')
        else:
            split_fields = fields

        if field_type == 'join':
            self.join_fields.extend([int(x) for x in split_fields if x is not None])
        elif field_type == 'compare':
            self.compare_fields.extend([int(x) for x in split_fields if x is not None])
        elif field_type == 'ignore':
            self.ignore_fields.extend([int(x) for x in split_fields if x is not None])
        else:
            raise ValueError('Invalid field_type value: %s' % field_type)

    def _validate_fields(self) -> None:
        if not self.join_fields:
            raise ValueError('key (join) fields are missing')

        # should add compare_fields to this check
        for field in self.ignore_fields:
            if field in self.join_fields:
                raise ValueError('invalid ignore_fields value: %s' % field)

        # should also confirm that compare_fields or ignore_fields are populated,
        # not both


    def compare_files(self,
                      old_fqfn: str,
                      new_fqfn: str,
                      dry_run: bool = False) -> None:
        """ Reads two sorted csv files, compares them based on a key, and
        writes results out to five output files.

        Args:
            old_fqfn: the fully-qualified file name of the old file
            new_fqfn: the fully-qualified file name of the new file
            dry_run:  a boolean, if True will not write output.  Defaults to
                      False
        Returns:
            nothing
        Raises:

        """
        self.dry_run = dry_run
        self.new_fqfn = new_fqfn
        self.old_fqfn = old_fqfn

        assert isfile(old_fqfn)
        assert isfile(new_fqfn)

        compare_fields = self.compare_fields
        ignore_fields = self.ignore_fields

        self._validate_fields()

        # set up input csv readers
        old_f = open(old_fqfn, 'r')
        self.old_csv = csv.reader(old_f, dialect=self.dialect)
        new_f = open(new_fqfn, 'r')
        self.new_csv = csv.reader(new_f, dialect=self.dialect)

        # set up output files, counts and writers
        for outtype in OUTPUT_TYPES:
            self.out_fqfn[outtype] = pjoin(self.out_dir, self._get_name(new_fqfn, outtype))
            self.out_file[outtype] = open(self.out_fqfn[outtype], 'w')
            self.out_writer[outtype] = csv.writer(self.out_file[outtype],
                                                  dialect=self.dialect)
        # prime the main loop
        self._read_old_csv()
        self._read_new_csv()

        while self.old_rec and self.new_rec:
            key_match_result = self._key_match()
            if key_match_result == 'new-greater':
                self._writer('delete', self.old_rec)
                self._read_old_csv()
            elif key_match_result == 'old-greater':
                self._writer('insert', self.new_rec)
                self._read_new_csv()
            else:
                if self._data_match(ignore_fields, compare_fields):
                    self._writer('same', self.old_rec)
                else:
                    self._writer('chgold', self.old_rec)
                    self._writer('chgnew', self.new_rec)
                self._read_new_csv()
                self._read_old_csv()

        while self.new_rec:
            self._writer('insert', self.new_rec)
            self._read_new_csv()

        while self.old_rec:
            self._writer('delete', self.old_rec)
            self._read_old_csv()

        old_f.close()
        new_f.close()
        for filename in self.out_file:
            self.out_file[filename].close()

    @staticmethod
    def _get_name(in_fn: str,
                  out_type: str) -> str:
        """ Gets the formatted name of an output file.
        Args:
            in_fn: input file name
            out_type: one of insert, delete, same, chgnew, chgold
        Returns:
            out_fn: which is the basename of in_fn, with .uniq or .sorted.uniq removed,
                    then with out_type added
        Notes:
            parsing is fragile should improve
        """
        fn = basename(in_fn)
        if fn.endswith('.sorted.uniq'):
            out_fn = fn[:-12]  #todo: make less fragile
        elif fn.endswith('.uniq'):
            out_fn = fn[:-5]   #todo: make less fragile
        elif fn.endswith('.sorted'):
            out_fn = fn[:-7]   #todo: make less fragile
        else:
            out_fn = fn
        return out_fn + '.' + out_type


    def _key_match(self) -> str:
        """ Determines if an old-file record matches a new-file record based
            on all the join-keys.
        Args:
            None
        Returns:
            result: equal if all keys match, new-greater if the new file's key
                    is greater than the old files, old-greater if the opposite.
        """
        for key in self.join_fields:
            if self.new_rec[key] > self.old_rec[key]:
                return 'new-greater'
            elif self.new_rec[key] < self.old_rec[key]:
                return 'old-greater'
        return 'equal'

    def _data_match(self,
                    ignore_fields: FieldPositionsType,
                    compare_fields: FieldPositionsType) -> bool:
        """ Determines if an old-file record matches a new-file record based
            on the non-join-keys.
        Args:
            ignore_fields: a list of fields to ignore represented as a list of
                           positions given a zero-offset.  If provided the
                           compare_fields cannot be provided - since all fields
                           not in this list will be compared.
            compare_fields: a list of fields to compare represented as a list
                           of positions given a zero-offset.  if provided the
                           ignore_fields cannot be provided - since all fields
                           not in this list will be ignored.
        Returns:
            result:  a boolean, if True the columns matched
        """
        # todo: pre-calc the list of fields to actually compare
        for index, _ in enumerate(self.new_rec):
            if index in self.join_fields:
                continue
            elif index in ignore_fields:
                continue
            elif compare_fields and index not in compare_fields:
                continue
            elif self.new_rec[index] != self.old_rec[index]:
                return False
        else:
            return True


    def _read_new_csv(self) -> None:
        """ Reads next rec from new file into self.new_rec
        Args:    None
        Returns: Nothing
        Notes:
            - Confirms sort order of file
            - Will assign None to self.new_rec at eof
        """
        try:
            last_rec = self.new_rec
            self.new_rec = self.new_csv.__next__()
            if last_rec is None: # first read priming
                last_rec = self.new_rec
            if len(last_rec) != len(self.new_rec):
                abort('new file has inconsistent number of fields', f'new_rec = {self.new_rec}')
            for key in self.join_fields:
                if self.new_rec[key] > last_rec[key]:
                    self.new_read_cnt += 1
                    break # good
                if self.new_rec[key] < last_rec[key]:
                    abort('ERROR: new file is not sorted correctly',
                          f'This refers to file {self.new_fqfn}, and key: {key}, and record: {self.new_rec} and last rec: {last_rec}')
        except StopIteration:
            self.new_rec = None


    def _read_old_csv(self) -> None:
        """ Reads next rec from new file into self.old_rec
        Args:    None
        Returns: Nothing
        Notes:
            - Confirms sort order of file
            - Will assign None to self.old_rec at eof
        """
        try:
            last_rec = self.old_rec
            self.old_rec = self.old_csv.__next__()
            if last_rec is None: # first read priming
                last_rec = self.old_rec
            if len(last_rec) != len(self.old_rec):
                abort('old file has inconsistent number of fields', f'old_rec = {self.new_rec}')
            for key in self.join_fields:
                if self.old_rec[key] > last_rec[key]:
                    self.old_read_cnt += 1
                    break # good
                if self.old_rec[key] < last_rec[key]:
                    abort('ERROR: old file is not sorted correctly',
                          f'This refers to file {self.old_fqfn}, and key: {key}, and record: {self.old_rec} and last rec: {last_rec}')
        except StopIteration:
            self.old_rec = None

    def _writer(self,
                outtype: str,
                outrec: RecordType) -> None:
        """" Run post-delta assignment then write record.
        Args:
            outtype - one of insert, delete, chgnew, chgold, same
            outrec - output list
        Returns: nothing
        """
        try:
            self.out_counts[outtype] += 1
        except KeyError:
            self.out_counts[outtype] = 1
        if not self.dry_run:
            adj_rec = self.dass.assign(outtype, outrec, self.old_rec, self.new_rec)
            self.out_writer[outtype].writerow(adj_rec)



class DeltaAssignments:
    """ Manages the post-delta transformations (aka assignments).
    """

    def __init__(self) -> None:
        self.assignments: Dict[str, Dict] = {} # supports minor transformations
        self.special_values: Dict[str, str] = {}
        self.seq: Dict[int, Dict[str, Any]] = {}

    def set_assignment(self,
                       dest_file: str,
                       dest_field: int,
                       src_type: str,
                       src_val: str = None,
                       src_file: str = None,
                       src_field: int = None) -> None:
        """ Write instructions for the assignment of a csv field in an output file.

        Args:
            dest_file: one of insert, delete, chgold or chgnew
            dest_field: the field position, given a zero-offset
            src_type: one of literal, copy, sequence, or special
            src_val: used by literal, lookup and sequence
            src_file: one of old, new or None
            src_field: the field position, given a zero-offset
        Returns:
            nothing
        Raises:
            ValueError if args are invalid
            sys.exit if sequence assignment is invalid
        """
        if dest_field:
            assert int(dest_field)
        if src_field:
            assert int(src_field)
        if dest_file not in ['insert', 'delete', 'chgold', 'chgnew', 'same']:
            raise ValueError('Invalid dest_file: %s' % dest_file)
        if not comm.isnumeric(dest_field):
            raise ValueError('Invalid dest_field: %s' % dest_field)
        if src_type not in ['literal', 'copy', 'sequence', 'special']:
            raise ValueError('Invalid src_type of %s' % src_type)
        if src_type in ['literal', 'lookup'] and src_val is None:
            raise ValueError('Missing src_val')
        if src_type == 'copy' and (src_file is None or src_field is None):
            raise ValueError('Missing src_file or src_field')
        if src_file not in [None, 'old', 'new']:
            raise ValueError('Invalid src_file: %s' % src_file)

        if dest_file not in self.assignments:
            self.assignments[dest_file] = {}
        self.assignments[dest_file][int(dest_field)] = {'src_type':src_type,
                                                        'src_val':src_val,
                                                        'src_file':src_file,
                                                        'src_field':src_field}
        if src_type == 'sequence':
            # note that seq validation does not check to see if same sequence was
            # refeenced twice with two different values.
            if src_file is not None and src_field is not None:
                tmp_val = None  # will get assigned based on file & field
            elif src_file is not None or src_field is not None:
                abort('Invalid sequence assignment config: src_file or src_field is None')
            elif src_val is None:
                tmp_val = 0
            elif comm.isnumeric(src_val):
                tmp_val = int(src_val)
            elif src_val in self.special_values:
                if comm.isnumeric(self.special_values[src_val]):
                    tmp_val = int(self.special_values[src_val])
                else:
                    abort('Sequence refers to invalid special variable'
                          'should be unique.  Variable: %s   Its value: %s'
                          % (src_val, self.special_values[src_val]))
            else:
                abort('Invalid src_val from config, must be numeric for sequence: %s'
                      ' or refer to special variable name '% src_val)

            self.seq[src_field] = {'start_val': tmp_val, 'last_val':  tmp_val}


    def set_special_values(self,
                           name: str,
                           value: str) -> None:
        """ Set special name-value for later assignment.

        Args:
            name:  name of special variable
            value: value of special variable
        Returns: nothing
        """
        self.special_values[name] = value


    def assign(self,
               outtype: str,
               outrec: RecordType,
               old_rec: RecordType,
               new_rec: RecordType) -> RecordType:
        """ Apply all assignment for a single rec.

        Args:
            outtype - one of insert, delete, same, chgold, chgnew
            outrec  - list of output record
            old_rec - list of old input record
            new_rec - list of new input record
        Returns:
            outrec - new version with assigned field
        Raises:
            sys.exit - if assignment fails
        """
        self.old_rec = old_rec
        self.new_rec = new_rec
        if outtype in self.assignments:
            for dest_field in self.assignments[outtype]:
                assigner = self.assignments[outtype][dest_field]
                try:
                    if assigner['src_type'] == 'literal':
                        outrec[dest_field] = assigner['src_val']
                    elif assigner['src_type'] == 'copy':
                        outrec[dest_field] = self._get_copy_value(assigner['src_file'],
                                                                  assigner['src_field'])
                    elif assigner['src_type'] == 'sequence':
                        outrec[dest_field] = self._get_seq_value(assigner['src_field'])
                    elif assigner['src_type'] == 'special':
                        outrec[dest_field] = self._get_special_value(assigner['src_val'])
                except (ValueError, IndexError) as err:
                    msg = f'assignments={assigner}, dest_field={dest_field}, outtype={outtype}'
                    abort(repr(err), msg, verbosity='debug')
        return outrec


    def _get_special_value(self, src_val: str) -> str:
        """ Get special variable value.
        Args:
            src_val - name of special variable
        Returns:
            value - value associated with variable name
        Raises:
            aborts if src_val not found
        """
        try:
            return self.special_values[src_val]
        except KeyError:
            abort(f'Invalid special value in assignment: {src_val}', json.dumps(self.special_values))


    def _get_copy_value(self, src_file: str, src_field: int) -> str:
        """" Get copy value from old or new source file.
        Args:
            src_file:  one of old, new
            src_field: zero-offset reference to field
        Returns:
            value
        Raises:
            ValueError if args are invalid
        """
        try:
            if src_file == 'old':
                if not self.old_rec:
                    raise ValueError('Assign-Copy refers to non-existing old_rec - invalid config')
                return self.old_rec[src_field]
            elif src_file == 'new':
                return self.new_rec[src_field]
            else:
                raise ValueError('Invalid src_file value: %s' % src_file)
        except IndexError:
            raise ValueError('Assign-Copy refers to non-existing field - invalid config or record')


    def _get_seq_value(self, src_field: int) -> str:
        """ Get the next sequence value from the source field.
        Args:
            src_field: zero-offset reference to field.
        Returns:
            sequence value
        """
        self.seq[src_field]['last_val'] += 1
        return str(self.seq[src_field]['last_val'])


    def set_sequence_starts(self,
                            dialect: csvhelper.Dialect,
                            old_fqfn: str) -> None:
        """ Sets all sequences to their starting values.

        Args:
            dialect: csv dialect of input files
            old_fqfn: fully-qualified old file name
        Returns:
            None
        Raises:
            sys.exit: if invalid values found in csv sequence field
        """
        for key in self.seq:
            if self.seq[key]['start_val'] is None:
                break
        else:
            return # all sequences already have a starting val

        old_rec_cnt = 0
        with open(old_fqfn, 'rt') as infile:
            reader = csv.reader(infile, dialect)
            for rec in reader:
                old_rec_cnt += 1
                for src_field in self.seq:
                    if self.seq[src_field]['last_val'] is not None:
                        continue # set already by config
                    elif rec[src_field].strip() == '':
                        continue # old file lacks good sequence val in this rec
                    try:
                        new_val = int(rec[src_field])
                    except ValueError:
                        abort('Non-integer value within sequence field: %s' % rec[src_field])
                    if old_rec_cnt == 1:
                        self.seq[src_field]['start_val'] = new_val
                    elif new_val > self.seq[src_field]['start_val']:
                        self.seq[src_field]['start_val'] = new_val

        # for any sequences set by the loop through the file, now we
        # can set their last_val:
        for src_field in self.seq:
            if (self.seq[src_field]['last_val'] is None
                    and self.seq[src_field]['start_val'] is not None):
                self.seq[src_field]['last_val'] = self.seq[src_field]['start_val']

        # if any sequences are stil None - it's because of an empty old file
        # or no valid starting sequences found in old file.
        # Set empty file to 0 otherwise abort.
        for src_field in self.seq:
            if (self.seq[src_field]['last_val'] is None
                    or self.seq[src_field]['start_val'] is None):
                if old_rec_cnt == 0:
                    self.seq[src_field]['last_val'] = 0
                    self.seq[src_field]['start_val'] = 0
                else:
                    abort('Logic Error: no starting sequence found in old file')
