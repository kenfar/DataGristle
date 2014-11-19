#!/usr/bin/env python

import os
import sys
from os.path import isfile, isdir, exists
from os.path import dirname, basename
from os.path import join  as pjoin
import csv
import fileinput
import collections
from pprint import pprint as pp

import psycopg2       as dbapi2
import logging
import envoy
import gristle.common as comm
from gristle.common import abort as abort

OUTPUT_TYPES = ['insert', 'delete', 'same', 'chgnew', 'chgold']


class FileDelta(object):

    def __init__(self, out_dir, dialect):
        """
        """
        self.out_dir         = out_dir
        self.dialect         = dialect
        self.join_fields     = []
        self.compare_fields  = []
        self.ignore_fields   = []
        self.dry_run         = False
        self.old_rec         = None
        self.new_rec         = None

        self.read_new_cnt = 0
        self.read_old_cnt = 0
        self.out_file     = {}
        self.out_fqfn     = {}
        self.out_writer   = {}
        self.out_counts   = collections.defaultdict(int)
        self.dass         = DeltaAssignments()

    def set_fields(self, field_type, *fields):
        """ assigns fields to joins, compares and ignores lists.
            inputs:
                field_type - must be 'join', 'compare' or 'ignore'
                *fields - the list of 0-offset field numbers.  Multiple
                    representations are accepted:
                    - string:          '0,1,3'
                    - list of numbers: 0,1,3
                    - list of strings: '0', '1', '3'
                    - single number:   0
                    - single string:   '0'
        """
        print 'field type: %s' % field_type
        print 'fields: '
        print fields
        assert field_type in ['join', 'compare', 'ignore']
        if len(fields) == 1 and ',' in str(fields[0]):
            split_fields = fields[0].split(',')
        else:
            split_fields = fields

        if field_type == 'join':
            for field in split_fields:
                if field is not None:
                    self.join_fields.append(int(field))
        elif field_type == 'compare':
            for field in split_fields:
                if field is not None:
                    print 'field: '
                    print field
                    self.compare_fields.append(int(field))
        elif field_type == 'ignore':
            for field in split_fields:
                if field is not None:
                    self.ignore_fields.append(int(field))
        else:
            assert 1/0, 'Invalid field_type value'



    def compare_files(self, old_fqfn, new_fqfn, compare_fields=None, ignore_fields=None,

                      dry_run=False):

        self.dry_run = dry_run
        # validate inputs
        assert isfile(old_fqfn)
        assert isfile(new_fqfn)

        #self.set_fields('compare', compare_fields)
        #self.set_fields('ignore', ignore_fields)
        compare_fields = self.compare_fields
        ignore_fields = self.ignore_fields

        for field in ignore_fields:
            if field in self.join_fields:
                raise ValueError, 'invalid ignore_fields value: %s' % field

        # set up input csv readers
        old_f           = open(old_fqfn, 'r')
        self.old_csv    = csv.reader(old_f,    dialect=self.dialect)
        new_f           = open(new_fqfn, 'r')
        self.new_csv    = csv.reader(new_f,    dialect=self.dialect)

        # set up output files, counts and writers
        for outtype in OUTPUT_TYPES:
            self.out_fqfn[outtype]   = pjoin(self.out_dir, self._get_name(new_fqfn, outtype))
            self.out_file[outtype]   = open(self.out_fqfn[outtype], 'w')
            self.out_writer[outtype] = csv.writer(self.out_file[outtype],
                                                  dialect=self.dialect)
        # prime the main loop
        self._read_old_csv()
        self._read_new_csv()

        while self.old_rec or self.new_rec:
            if not self.old_rec:
                self._writer('insert', self.new_rec)
                self._read_new_csv()
            elif not self.new_rec:
                self._writer('delete', self.old_rec)
                self._read_old_csv()
            else:
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
                        self._writer('chgnew', self.old_rec)
                    self._read_new_csv()
                    self._read_old_csv()

        old_f.close()
        new_f.close()
        for filename in self.out_file:
            self.out_file[filename].close()

    def _get_name(self, in_fn, out_type):
        fn = basename(in_fn)
        if fn.endswith('.sorted.uniq'):
            out_fn = in_fn[:-12]
        elif fn.endswith('.uniq'):
            out_fn = in_fn[:-5]
        else:
            out_fn = fn
        return out_fn + '.' + out_type


    def _key_match(self):
        for key in self.join_fields:
            if self.new_rec[key] > self.old_rec[key]:
                return 'new-greater'
            elif self.new_rec[key] < self.old_rec[key]:
                return 'old-greater'
        return 'equal'

    def _data_match(self, ignore_fields, compare_fields):
        for index in range(len(self.new_rec)):
            #idx_off1 = index+1
            if index in self.join_fields:
                continue
            elif index in ignore_fields:
                continue
            elif compare_fields and index not in compare_fields:
                continue
            elif self.new_rec[index] != self.old_rec[index]:
                return False
            #else it matches, keep looking for a match failure
        else:
            return True

    def _read_new_csv(self):
        try:
            last_rec     = self.new_rec
            self.new_rec = self.new_csv.next()
            if last_rec is None: # first read priming
                last_rec = self.new_rec
            if len(last_rec) != len(self.new_rec):
                abort('new file has inconsistent number of fields')
            for key in self.join_fields:
                if self.new_rec[key] > last_rec[key]:
                    break # good
                if self.new_rec[key] < last_rec[key]:
                    print self.new_rec
                    print 'key: %s' % key
                    abort('new file is not sorted correctly')
        except StopIteration:
            self.new_rec = None

    def _read_old_csv(self):
        try:
            last_rec     = self.old_rec
            self.old_rec = self.old_csv.next()
            if last_rec is None: # first read priming
                last_rec = self.old_rec
            if len(last_rec) != len(self.old_rec):
                abort('old file has inconsistent number of fields')
            for key in self.join_fields:
                if self.old_rec[key] > last_rec[key]:
                    break # good
                if self.old_rec[key] < last_rec[key]:
                    print self.old_rec
                    print 'key: %s' % key
                    abort('old file is not sorted correctly')
        except StopIteration:
            self.old_rec = None

    def _writer(self, outtype, outrec):
        self.out_counts[outtype] += 1
        if not self.dry_run:
            adj_rec = self.dass.assign(outtype, outrec, self.old_rec, self.new_rec)
            self.out_writer[outtype].writerow(adj_rec)



class DeltaAssignments(object):

    def __init__(self):
        self.assignments    = {} # supports minor transformations
        self.special_values = {}
        self.seq            = {}

    def set_assignment(self, dest_file, dest_field, src_type,
                       src_val=None, src_file=None, src_field=None,
                       comment=None):
        if dest_file not in ['insert', 'delete', 'chgold', 'chgnew']:
            raise ValueError, 'Invalid dest_file: %s' % dest_file
        if not comm.isnumeric(dest_field):
            raise ValueError, 'Invalid dest_field: %s' % dest_field
        if src_type not in ['literal', 'copy', 'lookup', 'sequence', 'special']:
            raise ValueError, 'Invalid src_type of %s' % src_type
        if src_type in ['literal', 'lookup'] and src_val is None:
            raise ValueError, 'Missing src_val'
        if src_type == 'copy' and (src_file is None or src_field is None):
            raise ValueError, 'Missing src_file or src_field'
        if src_file not in [None, 'old', 'new']:
            raise ValueError, 'Invalid src_file: %s' % src_file
        #self.assignments[(dest_file, int(dest_field))] = {'src_type':src_type,
        if dest_file not in self.assignments:
            self.assignments[dest_file] = {}
        self.assignments[dest_file][int(dest_field)] = {'src_type':src_type,
                                                        'src_val':src_val,
                                                        'src_file':src_file,
                                                        'src_field':src_field}
        if src_type == 'sequence':
            # note that seq validation does not check to see if same sequence was
            # refeenced twice with two different values.
            if src_val is not None:
                if not comm.isnumeric(src_val):
                    abort('Invalid src_val from config, must be numeric for sequence: %s' % src_val)
            tmp_val = int(src_val) if comm.isnumeric(src_val) else None
            self.seq[src_field] = {'start_val': tmp_val,
                                   'last_val':  tmp_val}


    def set_special_values(self, name, value):
        self.special_values[name] = value


    def assign(self, outtype, outrec, old_rec, new_rec):
        self.old_rec = old_rec
        self.new_rec = new_rec
        if outtype in self.assignments:
            for dest_field in self.assignments[outtype]:
                assigner = self.assignments[outtype][dest_field]
                try:
                    if assigner['src_type']   == 'literal':
                        outrec[dest_field-1]  = assigner['src_val']
                    elif assigner['src_type'] == 'copy':
                        outrec[dest_field-1]  = self._assign_copy(assigner['src_file'],
                                                                assigner['src_field'])
                    elif assigner['src_type'] == 'sequence':
                        outrec[dest_field-1]  = self._assign_seq(assigner['src_field'])
                    elif assigner['src_type'] == 'special':
                        outrec[dest_field-1]  = self._assign_special(assigner['src_val'])
                except ValueError, e:
                    abort(e)
        return outrec


    def _assign_special(self, src_val):
        try:
            return self.special_values[src_val]
        except KeyError:
            abort('Invalid special value referenced in assignment: %s' % src_val)


    def _assign_copy(self, src_file, src_field):
        if not self.old_rec:
            raise ValueError, 'Assign-Copy refers to non-existing old_rec - invalid config'
        try:
            if src_file == 'old':
                return self.old_rec[src_field-1]
            elif src_file == 'new':
                return self.new_rec[src_field-1]
            else:
                raise ValueError, 'Invalid src_file value: %s' % src_file
        except IndexError:
            raise ValueError, 'Assign-Copy refers to non-existing field - invalid config or record'


    def _assign_seq(self, src_field):
        self.seq[src_field]['last_val']  += 1
        print 'assigned, updated seq: '
        pp(self.seq)
        return str(self.seq[src_field]['last_val'])

    def get_sequence_starts(self, dialect, old_fqfn):
        for key in self.seq.keys():
            if self.seq[key]['start_val'] is None:
                break
        else:
            return # all sequences already have a starting val

        old_rec_cnt = 0
        for rec in csv.reader(fileinput.input(old_fqfn), dialect):
            for src_field in self.seq:
                if self.seq[src_field]['last_val'] is not None:
                    continue # set already by config
                try:
                    new_val = int(rec[src_field])
                except ValueError:
                    abort('Non-integer value within sequence field: %s' % rec[src_field])
                if fileinput.lineno() == 1:
                    self.seq[src_field]['start_val'] = new_val
                elif new_val > self.seq[src_field]['start_val']:
                    self.seq[src_field]['start_val'] = new_val
            old_rec_cnt = fileinput.lineno()

        # for any sequences set by the loop through the file, now we
        # can set their last_val:
        for src_field in self.seq:
            if self.seq[src_field]['last_val'] is None:
                self.seq[src_field]['last_val'] = self.seq[src_field]['start_val']

        # if any sequences are stil None - it's because of an empty old file
        # set these to 0
        for src_field in self.seq:
            if (self.seq[src_field]['last_val'] is None
                    or self.seq[src_field]['start_val'] is None):
                if old_rec_cnt == 0:
                    self.seq[src_field]['last_val'] = 0
                    self.seq[src_field]['start_val'] = 0
                else:
                    abort('Logic Error: empty old file and sequence is None')






