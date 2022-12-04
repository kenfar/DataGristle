#!/usr/bin/env python
""" Contains standard io reading & writing code

    See the file "LICENSE" for the full license governing this code.
    Copyright 2017-2022 Ken Farmer
"""
import csv
import datetime as dt
import errno
import io
import os
from os.path import join as pjoin, getsize
from pprint import pprint as pp
import random
import sys
import tempfile
import time
from typing import Optional, Union

from datagristle import csvhelper
from datagristle import metadata



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
                 files: list[str],
                 dialect: csvhelper.Dialect,
                 return_header: bool = False) -> None:

        self.files = files
        self.dialect = dialect
        self.return_header = return_header
        self.use_cache = True                  # set to False, mostly for testing

        self.header: list[str] = []
        self.field_names: list[str] = []       # not populated until after a rec is read
        self.first_rec: list[Union[str, float]] = []
        self.files_read = 0
        self.rec_cnt = 0                       # does not count header records
        self.curr_file_rec_cnt = 0             # does not count header records
        self.infile = None
        self.eof = False
        self.md = metadata.GristleMetaData()

        # If dialect.has_header==True then it will try to read the header.  If the file is empty
        # we could get a stop iteration here.  Instead lets just leave self.header empty and let
        # the calling program pick up StopIteration on its first read.
        try:
            self._open_next_input_file()
        except StopIteration:
            pass


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


    def __next__(self,
                 skip_to_end=False):
        """ Returns the next input record.   Can handle data piped in as well
            as multiple input files.   All data is assumed to be csv files.
        """
        while True:
            try:
                if skip_to_end:
                    raise StopIteration
                return self._read_next_rec()
            except StopIteration:   # end of file, loop around and get another
                if self.files[0] == '-' and self.files_read == 1 and self.curr_file_rec_cnt == 0:
                    sys.exit(errno.ENODATA)
                self.infile.close()
                try:
                    self._open_next_input_file()  # will raise StopIteration if out of files
                except StopIteration:
                    self.eof = True
                    raise


    def _read_next_rec(self) -> list[str]:

        rec = self.csv_reader.__next__()
        if self.rec_cnt == 0:
            self.first_rec = rec
            self._determine_field_names()
        self.rec_cnt += 1
        self.curr_file_rec_cnt += 1
        return rec


    def close(self) -> None:
        if self.files[0] != '-' and self.infile:
            self.infile.close()


    def reset(self) -> None:
        """ Resets the Handler back at the start of the first file.

        Is used when processing files multiple times, for example, when
        first reading to get a file count for the slicer specs, and then
        to read again.
        """
        self.close()
        self.files_read = 0
        self.rec_cnt = 0                # does not count header records
        self.curr_file_rec_cnt = 0      # does not count header records
        try:
            self._open_next_input_file()
        except StopIteration:
            pass


    def get_field_count(self):
        self._determine_field_names()
        return len(self.field_names)


    def get_rec_count(self,
                      read_limit: int = -1) -> tuple[int, bool]:
        """ Returns the number of records in the file

        Args:
            read_limit: If provided then reads up to the read_limit and then estimates
                        the remaining records.  Defaults to -1, which means no limit.
        Returns:
            rec count:  Count of rows read
            estimated:  True or False, indicates if the rec count is an estimation based
                        on the first self.read_limit rows.
        """
        byte_cnt = 0
        estimated_rec_cnt = 0
        estimated = False
        read_limit_hit = False

        # First check to see if we have cached the exact row count for a single file:
        if len(self.files) == 1 and self.files[0] != '-' and self.use_cache:
            temp_rec_cnt = self.md.file_index_tools.get_rec_count(filename=self.files[0])
            if temp_rec_cnt >= 0:
                return temp_rec_cnt, estimated

        # fast method, should be helpful if the files are very large
        if read_limit > -1:
            estimated = True
            try:
                while True:
                    rec = self.__next__()
                    byte_cnt += (len(''.join(rec)) + len(rec) + 1)
                    if self.rec_cnt  > read_limit:
                        read_limit_hit = True
                        break
            except StopIteration:
                pass
            if read_limit_hit is False:
                return self.rec_cnt, estimated
            else:
                try:
                    bytes_per_rec = byte_cnt / self.rec_cnt
                    total_file_size = sum([int(getsize(x)) for x in self.files if x != '-' ])
                    estimated_rec_cnt = int(total_file_size / bytes_per_rec)
                except  ZeroDivisionError:
                    pass
                return estimated_rec_cnt, estimated

        # slowest method, but most accurate
        try:
            while True:
                _ = self.__next__()
        except StopIteration:
            pass

        if len(self.files) == 1 and self.use_cache:
            mod_datetime, file_size = get_file_info(self.files[0])
            if self.header:
                col_cnt = len(self.header)
            else:
                col_cnt = len(self.first_rec)
            self.md.file_index_tools.set_counts(filename=self.files[0],
                                                mod_datetime=mod_datetime,
                                                file_bytes=file_size,
                                                rec_count=self.rec_cnt,
                                                col_count=col_cnt)
        return self.rec_cnt, estimated



    def _determine_field_names(self) -> None:
        """ Determines names of fields

        Must be run after the program has read a record.

        """
        if self.header:
            self.field_names = self.header
        elif self.first_rec:
            self.field_names = [f'field_{x}' for x in range(len(self.first_rec))]
        else:
            # May not have read a rec yet - maybe got the rec count from metadata
            # So, lets read a rec and then start over.  This won't work for stdin,
            # but should be fine for reading files.
            # raise InvalidSequence('Cannot access fields until a rec is read')
            self.__next__()
            if self.header:
                self.field_names = self.header
            elif self.first_rec:
                self.field_names = [f'field_{x}' for x in range(len(self.first_rec))]
            else:
                raise ValueError('Logic Error: not finding first rec or header!')
            self.reset()



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

        self.output_filename = output_filename.strip()
        self.dry_run = dry_run
        self.random_out = random_out
        self.dialect = dialect
        self.rec_cnt = 0
        if self.output_filename == '-':
            self.outfile = default_output
        else:
            self.outfile = open(self.output_filename, mode, encoding='utf-8', newline='')
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
                  record: list[str]) -> None:
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
                      record: list[str]) -> None:
        self.write_rec(record)


    def write_text_rec(self,
                       record: str) -> None:
        self.outfile.write(record)



    def close(self):
        if self.output_filename != '-':
            self.outfile.close()



def get_file_size(files):
    tot_size = int(sum([os.path.getsize(fn)
                        for fn in files
                        if fn != '-']))
    return tot_size



def get_rec_count(files: list[str],
                  dialect: csv.Dialect) -> Optional[int]:
    """ Get record counts for input files.
        - Counts have an offset of 0
    """
    rec_cnt = 0
    if files[0] == '-':
        return None

    for fn in files:
        with open(fn, 'r', newline='', encoding='utf-8') as inbuf:
            csv_reader = csv.reader(inbuf, dialect=dialect)
            for _ in csv_reader:
                rec_cnt += 1
    return rec_cnt



def remove_all_temp_files(prefix: str,
                          min_age_hours: float) -> None:

    tmpdir = tempfile.gettempdir()
    min_age_seconds = min_age_hours * 60 * 60

    for fn in os.listdir(tmpdir):
        if not fn.startswith(prefix):
            continue
        seconds = time.time() - os.path.getmtime(pjoin(tmpdir, fn))
        if seconds >= min_age_seconds:
            os.remove(pjoin(tmpdir, fn))



def get_file_info(filename):
    file_timestamp = os.path.getmtime(filename)
    file_dt = dt.datetime.fromtimestamp(file_timestamp)
    file_size = os.path.getsize(filename)
    return file_dt, file_size



class InvalidSequence(Exception):
    pass
