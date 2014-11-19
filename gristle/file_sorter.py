#!/usr/bin/env python

import os
import sys
from os.path import isfile, isdir, exists
from os.path import dirname, basename
from os.path import join  as pjoin
import csv

import envoy
import gristle.common as comm




class CSVSorter(object):


    def __init__(self, dialect, join_fields_0off, tmp_dir=None, out_dir=None):

        assert dialect          is not None
        assert join_fields_0off is not None
        self.dialect = dialect

        if tmp_dir:
            if isdir(tmp_dir):
                self.tmp_dir = tmp_dir
            else:
                raise ValueError, 'Invalid sort temp directory: %s' % tmp_dir
        else:
            self.tmp_dir = tmp_dir

        if out_dir:
            if isdir(out_dir):
                self.out_dir = out_dir
            else:
                raise ValueError, 'Invalid sort output directory: %s' % out_dir
        else:
            self.out_dir = out_dir

        try:
            join_fields_1off = [ int(x)+1 for x in join_fields_0off ]
        except ValueError:
            print 'Error: invalid non-numeric sort key: %s' % join_fields_0off
            raise

        self.field_opt = ''
        for field in join_fields_1off:
            self.field_opt += ' -k %s' % field
        self.sort_del = self._get_sort_del(self.dialect.delimiter)


    def sort_file(self, in_fqfn, out_fqfn=None):
        """ Inputs:
               - in_fn
               - out_fn
               - key_pos_list: list of
        """
        tmp_dir  = self.tmp_dir or dirname(in_fqfn)
        if not out_fqfn:
            out_dir  = self.out_dir or dirname(in_fqfn)
            out_fqfn = pjoin(out_dir, basename(in_fqfn) + '.sorted')

        if not isfile(in_fqfn):
            raise ValueError, 'Invalid input file: %s' % in_fqfn

        cmd = ''' sort  %s                 \
                        --field-separator %s \
                        -T  %s             \
                        %s                 \
                        -o  %s             \
              ''' % (self.field_opt, self.sort_del, self.tmp_dir, in_fqfn, out_fqfn)
        r = envoy.run(cmd)
        if r.status_code != 0:
            print cmd
            print r.std_err
            print r.std_out
            raise IOError, 'Invalid sort status code: %d' % r.status_code
        return out_fqfn

    def _get_sort_del(self, delimiter):

        if delimiter == '\t':
            return "$'\t'"
            #alternative, got stuck on envoy i think:
            #return ''' " `echo '\t'` " ''' 
        else:
            return "'%s'" % delimiter

