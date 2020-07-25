#!/usr/bin/env python
""" Contains standard io reading & writing code

    See the file "LICENSE" for the full license governing this code.
    Copyright 2017-2020 Ken Farmer
"""
import os
import sys
import csv
import io
import random
import errno
from os.path import isfile
from pprint import pprint
from typing import Union, Dict, List, Tuple, Any, Optional
from pprint import pprint as pp

import datagristle.csvhelper as csvhelper
import datagristle.file_type as file_type



class InputHandler(object):

    def __init__(self,
                 files: List[str],
                 dialect) -> None:

        self.dialect = dialect
        self.files = files
        self.files_read = 0
        self.rec_cnt = 0
        self.curr_file_rec_cnt = 0
        self.infile = None
        self.input_stream = None
        self._open_next_input_file()

    def seek(self, offset):
        return self.input_stream.seek(offset)

    def tell(self):
        return self.input_stream.tell()

    def _open_next_input_file(self):

        if self.files[0] == '-' and self.files_read == 0:

            if os.isatty(0):  # checks if data was pipped into stdin
                #raise ValueError, "No files or stdin provided"
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



# correct behavior?
# if has_header - generally ignore header in processing:
#   slicer
#   freaker
#   determinator
#   differ
# if has_header - then record counts generally start at 2nd record
# if has_header - then ignore header in each file if multiple files
# if has_header - then copy it on output when output is also a csv:
#   slicer?  not unless we have an output-header column?
#   differ?  not unless we have a output-header column?


    def __iter__(self):
        return self


    def __next__(self):
        """ Returns the next input record.   Can handle data piped in as well
            as multiple input files.   All data is assumed to be csv files.
        """
        while True:
            try:
                rec = self._read_next_rec()
                return rec
            except StopIteration:   # end of file, loop around and get another
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
                 default_output = sys.stdout,
                 dry_run: bool = False,
                 random_out: float = 1.0):

        assert default_output in (sys.stdout, sys.stderr), "invalid default_output: {}".format(default_output)
        assert 0.0 <= random_out <= 1.0

        self.output_filename = output_filename
        self.dry_run = dry_run
        self.random_out = random_out
        self.dialect = dialect
        self.rec_cnt = 0
        if self.output_filename == '-':
            #print('*************** writing to stdout *******************')
            self.outfile = default_output
        else:
            self.outfile = open(output_filename, "wt", encoding='utf-8')
        if dialect:
            self.writer = csv.writer(self.outfile, dialect=dialect)
        else:
            self.writer = None


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



