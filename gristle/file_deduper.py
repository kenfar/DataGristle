#!/usr/bin/env python

import os
import sys
from os.path import isfile, isdir, exists
from os.path import dirname, basename
from os.path import join  as pjoin
import csv
import fileinput

import envoy
import gristle.common as comm


class CSVDeDuper(object):
    """ Read sorted csv file and write non-duplicates to another csv file
        based on key fields.

    Args:
        dialect:   csv dialect
        key_fields_0off: positions of key fields, based on zero-offset
        out_dir:  directory for output file.  Default is input file's
        directory.
    Raises:
        ValueError: if key fields are invalid (ex: non-numeric)
        ValueError: if out_dir is invalid (ex: doesn't exist)
    """

    def __init__(self, dialect, key_fields_0off, out_dir=None):

        assert dialect         is not None
        assert key_fields_0off is not None

        self.dialect    = dialect

        try:
            self.key_fields_0off = [ int(x) for x in key_fields_0off ]
        except ValueError:
            print 'Error: invalid non-numeric sort key: %s' % key_fields_0off
            raise

        if out_dir:
            if isdir(out_dir):
                self.out_dir = out_dir
            else:
                raise ValueError, 'Invalid sort output directory: %s' % out_dir
        else:
            self.out_dir = None


    def dedup_file(self, in_fqfn, out_fqfn=None):
        """ Copy non-duplicated records from csv input file to csv output file.

        Args:
            in_fqfn: the fully-qualified file name for the sorted input csv file
            out_fqfn: the fully-aualified file name for the sorted output csv
            file.  If none is provided it will use the in_fqfn + .uniq
        Returns:
            out_fqfn:  output fully-qualified filename
            read_cnt:  count of records read
            write_cnt: count of records written
        Notes:
            - The number of duplicates dropped can be derrived by subtracting
              the write count from the read count.
            - Unlike some utilities this tool will not remove all copies of a
              duplicate - just enough to drop the number to a single instance.
              For example, if there are three records with a key of 'aaa', two
              will be dropped and the program will write one to the output
              file.
        """
        if not out_fqfn:
            out_dir  = self.out_dir or dirname(in_fqfn)
            out_fqfn = pjoin(out_dir, basename(in_fqfn) + '.uniq')

        # walk through input file, dropping duplicates
        outfile   = open(out_fqfn, 'w')
        outwriter = csv.writer(outfile, dialect=self.dialect)
        last_rec  = None
        write_cnt = 0
        for rec in csv.reader(fileinput.input(in_fqfn), dialect=self.dialect):
            if last_rec:
                for key in self.key_fields_0off:
                    if rec[key] != last_rec[key]:
                         break
                else:
                    continue  # duplicate
            write_cnt += 1
            outwriter.writerow(rec)
            last_rec = rec
        read_cnt = fileinput.lineno()
        outfile.close()
        fileinput.close()
        return (out_fqfn, read_cnt, write_cnt)





