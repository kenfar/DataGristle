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
    """ Input File Reader

    Example usage:
        input_handler = file_io.InputHandler(nconfig.infiles,
                                             nconfig.dialect,
                                             return_header=True)
    Notes:
        - dialect: if None will not treat file as csv
        - dialect.has_header if True it will read the header into self.header, then skip
          ahead to the next record and return that.
        - if return_header==True then the first read will be of the header record.  This is
          helpful for programs that need it - like gristle_slicer & gristle_viewer.  Otherwise,
          the header is not returned, but simply kept within self.header.
    """


    def __init__(self,
                 files: List[str],
                 dialect: csvhelper.Dialect,
                 return_header: bool = False) -> None:

        self.dialect = dialect
        self.header: List[str] = []
        self.return_header = return_header
        self.files = files
        self.files_read = 0
        self.rec_cnt = 0                # does not count header records
        self.curr_file_rec_cnt = 0      # does not count header records
        self.infile = None

        # If dialect.has_header==True then it will try to read the header.  If the file is empty
        # we could get a stop iteration here.  Instead lets just leave self.header empty and let 
        # the calling program pick up StopIteration on its first read.
        try:
            self._open_next_input_file()
        except StopIteration:
            pass

#    No longer used - probably because seeking around a csv doesn't work well - because
#    of newlines.  But lets keep it here for a bit, because we may be adding other file types soon.
#    self.input_stream = None
#    def seek(self, offset):
#        return self.input_stream.seek(offset)
#    def tell(self):
#        return self.input_stream.tell()

    def _open_next_input_file(self):

        def handle_header():
            if self.dialect.has_header and not self.return_header:
                self.header = self.csv_reader.__next__()

        if self.files[0] == '-' and self.files_read == 0:
            # This will only run once
            if os.isatty(0):  # checks if data was piped into stdin
                sys.exit(errno.ENODATA)
            input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', newline='')
            self.csv_reader = csv.reader(input_stream, dialect=self.dialect)
            self.infile = sys.stdin
            self.files_read = 1
            self.curr_file_rec_cnt = 0
            handle_header()
        elif self.files_read < len(self.files):
            self.infile = open(self.files[self.files_read - 1], 'rt', newline='', encoding='utf-8')
            self.csv_reader = csv.reader(self.infile, dialect=self.dialect)
            self.files_read += 1
            self.curr_file_rec_cnt = 0
            handle_header()
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
                if self.files[0] == '-' and self.files_read == 1 and self.curr_file_rec_cnt == 0:
                    sys.exit(errno.ENODATA)
                self.infile.close()
                self._open_next_input_file()  # will raise StopIteration if out of files


    def _read_next_rec(self):

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
