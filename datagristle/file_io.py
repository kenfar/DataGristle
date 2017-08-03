#!/usr/bin/env python
""" Contains standard io reading & writing code

    See the file "LICENSE" for the full license governing this code.
    Copyright 2017 Ken Farmer
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
                 delimiter: Optional[str],
                 quoting: Optional[str],
                 quotechar: Optional[str],
                 has_header: Optional[bool]) -> None:

        self.files = files
        self.files_read = 0
        self.rec_cnt = 0
        self.dialect = self._get_dialect(files,
                                         delimiter,
                                         quoting,
                                         quotechar,
                                         has_header)
        if files[0] == '-':
            if os.isatty(0):  # checks if data was pipped into stdin
                #raise ValueError, "No files or stdin provided"
                sys.exit(errno.ENODATA)
            else:
                input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', newline='')
                self.csv_reader = csv.reader(input_stream, dialect=self.dialect)
                self.infile = sys.stdin
                self.files_read = 1
        else:
            self.infile = open(files[0], 'rt', newline='', encoding='utf-8')
            self.csv_reader = csv.reader(self.infile, dialect=self.dialect)
            self.files_read = 1



    def _get_dialect(self,
                     infiles: List[str],
                     delimiter: Optional[str],
                     quoting: Optional[str],
                     quotechar: Optional[str],
                     has_header: Optional[bool]) -> csvhelper.Dialect:
        if delimiter:
            dialect = csvhelper.Dialect(delimiter=delimiter,
                                        has_header=has_header,
                                        quoting=file_type.get_quote_number(quoting),
                                        quotechar=quotechar,
                                        lineterminator='\n')
        else:
            for infile in infiles:
                my_file = file_type.FileTyper(infile)
                try:
                    dialect = my_file.analyze_file()
                    break
                except file_type.IOErrorEmptyFile:
                    continue
            else:
                raise EOFError
        return dialect


    def __iter__(self):
        return self

    def __next__(self):
        """ Returns the next input record.   Can handle data piped in as well
            as multiple input files.   All data is assumed to be csv files.
        """
        try:
            rec = self.csv_reader.__next__()
            self.rec_cnt += 1
        except StopIteration:
            if self.files_read < len(self.files): # another file to read!
                self.files_read += 1
                self.infile = open(self.files[self.files_read - 1], 'rt', newline='', encodings='utf-8')
                self.csv_reader = csv.reader(self.infile, dialect=self.dialect)
                rec = self.csv_reader.next()
                self.rec_cnt += 1
            else:
                raise
        else:
            return rec


    def close(self):
        if self.files[0] != '-':
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
        if self.output_filename == '-':
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



