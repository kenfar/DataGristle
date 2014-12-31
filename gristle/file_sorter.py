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

    def __init__(self, dialect, key_fields_0off, tmp_dir=None, out_dir=None):

        assert dialect          is not None
        assert key_fields_0off  is not None

        self.dialect   = dialect
        self.sort_del  = self._get_sort_del(self.dialect.delimiter)

        if tmp_dir and not isdir(tmp_dir):
            raise ValueError, 'Invalid sort temp directory: %s' % tmp_dir
        else:
            self.tmp_dir = tmp_dir

        if out_dir and not isdir(out_dir):
            raise ValueError, 'Invalid sort output directory: %s' % out_dir
        else:
            self.out_dir = out_dir

        # convert from std datagristle 0offset to sort's 1offset
        try:
            key_fields_1off = [ int(x)+1 for x in key_fields_0off ]
        except ValueError:
            print 'Error: invalid non-numeric sort key: %s' % key_fields_0off
            raise

        self.field_opt = ''
        for field in key_fields_1off:
            self.field_opt += ' -k %s' % field


    def sort_file(self, in_fqfn, out_fqfn=None):
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

