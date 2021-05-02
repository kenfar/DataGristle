#!/usr/bin/env python
""" Contains standard io reading & writing code

    See the file "LICENSE" for the full license governing this code.
    Copyright 2017-2021 Ken Farmer
"""
import csv
import errno
import io
import os
from pprint import pprint as pp
import random
import sys
from typing import List

import datagristle.csvhelper as csvhelper



class InputHandler(object):

    def __init__(self,
                 files: List[str],
                 dialect: csvhelper.Dialect) -> None:

        self.dialect = dialect
        self.files = files
        self.files_read = 0
        self.rec_cnt = 0
        self.curr_file_rec_cnt = 0
        self.infile = None
        self.input_stream = None
        self._open_next_input_file()

#    No longer used - probably because seeking around a csv doesn't work well - because
#    of newlines
#    def seek(self, offset):
#        return self.input_stream.seek(offset)
#    def tell(self):
#        return self.input_stream.tell()

    def _open_next_input_file(self):

        if self.files[0] == '-' and self.files_read == 0:

            if os.isatty(0):  # checks if data was piped into stdin
                sys.exit(errno.ENODATA)

            self.input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', newline='')
            self.csv_reader = csv.reader(self.input_stream, dialect=self.dialect)
            self.infile = sys.stdin
            self.files_read = 1
            self.curr_file_rec_cnt = 1

        elif self.files_read < len(self.files):
            self.infile = open(self.files[self.files_read - 1], 'rt', newline='', encoding='utf-8')
            self.csv_reader = csv.reader(self.infile, dialect=self.dialect)
            self.files_read += 1
            self.curr_file_rec_cnt = 1
        else:
            raise StopIteration


    def __iter__(self):
        return self


    def __next__(self):
        """ Returns the next input record.   Can handle data piped in as well
            as multiple input files.   All data is assumed to be csv files.
        """
        while True:
            try:
                return self._read_next_rec()
            except StopIteration:   # end of file, loop around and get another
                if self.files[0] == '-' and self.files_read == 1 and self.curr_file_rec_cnt == 1:
                    sys.exit(errno.ENODATA)
                self.infile.close()
                self._open_next_input_file()  # will raise StopIteration if out of files


    def _read_next_rec(self):
        if self.curr_file_rec_cnt == 0 and self.dialect.has_header:
            self.header = self.csv_reader.__next__()
        rec = self.csv_reader.__next__()
        self.rec_cnt += 1
        self.curr_file_rec_cnt += 1
        return rec


    def close(self):
        if self.files[0] != '-' and self.infile:
            self.infile.close()




class OutputHandler(object):
    """ Handles all aspects of writing to output files: opening file,
        writing records, managing random writes, keeping counts,
        closing the file, etc.
    """

    def __init__(self,
                 output_filename: str,
                 dialect: csvhelper.Dialect,
                 default_output=sys.stdout,
                 dry_run: bool = False,
                 random_out: float = 1.0,
                 mode: str = 'wt'):

        assert default_output in (sys.stdout, sys.stderr), "invalid default_output: {}".format(default_output)
        assert 0.0 <= random_out <= 1.0

        self.output_filename = output_filename
        self.dry_run = dry_run
        self.random_out = random_out
        self.dialect = dialect
        self.rec_cnt = 0
        if self.output_filename == '-':
            self.outfile = default_output
        else:
            self.outfile = open(output_filename, mode, encoding='utf-8', newline='')
        if dialect:
            self.writer = csv.writer(self.outfile, dialect=dialect)
        else:
            self.writer = self.noncsv_writer(self.outfile)  # type: ignore


    class noncsv_writer:
        """ Provides a simple writer with a csv-like signature
        """

        def __init__(self,
                     outbuf):
            self.outbuf = outbuf

        def writerow(self,
                     record):
            self.outbuf.write(record)


    def write_rec(self,
                  record: List[str]) -> None:
        """ Write a record to output.
            If silent arg was provided, then write is suppressed.
            If randomout arg was provided, then randomly determine
               whether or not to write record.
        """
        if self.dry_run:
            return
        if self.random_out != 1.0:
            if random.random() > self.random_out:
                return
        try:
            self.writer.writerow(record)
            self.rec_cnt += 1
        except csv.Error:
            print('Invalid record: %s' % record)
            raise


    def write_csv_rec(self,
                      record: List[str]) -> None:
        self.write_rec(record)


    def write_text_rec(self,
                       record: str) -> None:
        self.outfile.write(record)



    def close(self):
        if self.output_filename != '-':
            self.outfile.close()
