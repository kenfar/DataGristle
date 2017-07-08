#!/usr/bin/env python

import subprocess
from os.path import isfile, isdir
from os.path import dirname, basename
from os.path import join  as pjoin
from typing import List

import datagristle.csvhelper as csvhelper



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
            print('Invalid sort return code: %s' % proc.returncode)
            print('delimiter: %s' % self.dialect.delimiter)
            raise IOError('invalid sort return code: %s, %s, %s' % (proc.returncode, stdout, stderr))

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

