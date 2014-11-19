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
        """ Inputs:
               - in_fqfn
               - out_fqfn
            Outputs:
               - fqfn of new file
               - read count
               - write count
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





