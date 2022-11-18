#!/usr/bin/env python
""" Contains standard io reading & writing code

    See the file "LICENSE" for the full license governing this code.
    Copyright 2017-2022 Ken Farmer
"""
import csv
import errno
import fileinput
import io
import os
from os.path import join as pjoin
from pprint import pprint as pp
import random
import sys
import tempfile
import time
from typing import List, Optional

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
        self.eof = False

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
                try:
                    self._open_next_input_file()  # will raise StopIteration if out of files
                except StopIteration:
                    self.eof = True
                    raise


    def _read_next_rec(self) -> List[str]:

        rec = self.csv_reader.__next__()
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



def get_file_size(files):
    tot_size = int(sum([os.path.getsize(fn)
                        for fn in files
                        if fn != '-']))
    return tot_size



def get_file_avg_rec_size(files, dialect):
    if files[0] == '-':
        return None

    rec_sizes = []
    rec_cnt = 0
    for fn in files:
        with open(fn, 'r', newline='', encoding='utf-8') as inbuf:
            csv_reader = csv.reader(inbuf, dialect=dialect)
            for rec in csv_reader:
                rec_sizes.append(get_rec_memory_size_mb(rec))
                rec_cnt += 1
                if rec_cnt > 1000:
                    break
            if rec_cnt > 1000:
                break
    fileinput.close()
    if rec_cnt == 0:
        return 0
    return int(sum([size for size in rec_sizes])/rec_cnt)



def get_rec_memory_size_mb(rec):
    return sum([sys.getsizeof(field) for field in rec])



def get_approx_rec_count(files):
    tot_size = get_file_size(files)
    rec_size = 0
    rec_cnt = 0
    for fn in files:
        if fn == '-':
            continue
        with open(fn, 'r') as inbuf:
            for rec in inbuf:
                rec_size += len(rec)
                rec_cnt += 1
                if rec_cnt > 1000:
                    break
    try:
        avg_rec_size = rec_size / rec_cnt
        approx_rec_cnt = tot_size / avg_rec_size
    except ZeroDivisionError:
        approx_rec_cnt = -1
    return approx_rec_cnt



def get_rec_count(files: List[str],
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



def get_file_approx_partitions(file_name):
    # first get file size
    #    - also get estimated number of records & record size ?
    # then determine the splits
    #    - 10m bytes
    #    - 100k records
    # then kick off multiple processes, each at one of the splits
    #    each then determines exact start, stop, record count
    # return:
    #    - each partition - start, stop, record-count
    #    - total record count

    file_size = os.path.getsize(file_name)
    #partition_size = 15
    #partition_size = 10 * 1024 * 1024  # 10 mbytes
    partition_size = 1024 * 1024  # 10 mbytes
    partition_number = int(file_size / partition_size)
    partition_starts = [x * partition_size for x in range(partition_number)]
    print('**** Runner setup **********************************')
    print(f'{file_size=}')
    print(f'{partition_starts=}')
    print(f'{partition_number=}')
    print(f'{partition_starts=}')
    print(f'{partition_starts[-1] - partition_size}')
    print(f'size of final partition: {file_size - partition_starts[-1]}')
    print([x/1024/1024 for x in partition_starts])
    print('****************************************************')

    parts = []
    for i, part_start in enumerate(partition_starts):
        try:
            part_stop = partition_starts[i+1]
        except IndexError:
            part_stop = None
        parts.append(file_partition_counter2(file_name,
                                             part_start,
                                             part_stop))
    print('\n********** file_partition_counter - complete ****************')
    pp(parts)
    print('*************************************************************')
    actual_part_starts = [(x[2], x[1]) for x in parts]


    recs = []
    for i, (part_start, part_stop) in enumerate(actual_part_starts):
        recs.append(file_partition_reader(file_name,
                                          part_start,
                                          part_stop))

    print('\n********** file_partition_reader - complete *****************')
    print(f'Count of partitions: {len(recs)}')
    print(f'Record counts by partition: {recs}')
    print(f'Sum of records in all partitions: {sum(recs)}')
    print('*************************************************************')



def file_partition_counter2(file_name,
                           partition_start,
                           partition_stop):

    print(f'======= file_partition_counter - {partition_start=}, {partition_stop=}  ===================')
    if partition_start == 0:
        return [0, partition_stop, 0]

    last_newline_offset = None
    with open(file_name, 'rb') as inbuf:
        read_bytes = 1000
        inbuf.seek(partition_start)
        data = inbuf.read(read_bytes)

        io_buf = io.BytesIO(data)
        rec = io_buf.read1(read_bytes)
        proposed_stop = None
        for i, byte in enumerate(rec):
            pp(byte)
            #if byte == b'\n':
            if byte == 10:
                actual_start = partition_start + i
                print('found it!!!!!!!!!!!!')
                break
    if actual_start:
        if partition_stop is None:
            pass
        elif actual_start >= partition_stop:
            raise ValueError
    else:
        raise ValueError
    return [partition_start, partition_stop, actual_start]




def file_partition_reader(file_name,
                          partition_start,
                          partition_stop):
    print(f'======= file_partition_reader - partition_start: {partition_start} stop: {partition_stop} ===================')
    recs = []
    # fixme: need to get next actual start!
    read_bytes = (partition_stop - partition_start)+1000 if partition_stop else 1_000_000
    pp(f'{read_bytes=}')

    with open(file_name, 'rt') as inbuf:
        inbuf.seek(partition_start)
        data = inbuf.read(read_bytes)

        #csv_reader = csv.reader(data)
        #for rec in csv_reader:
        str_buf = io.StringIO(data)
        for rec in csv.reader(str_buf):
            #pp(f'{rec=}')
            recs.append(rec)

        #csv_reader = csv.reader(inbuf)
        #for rec in csv_reader:
        #    last_offset = inbuf.tell()
        #    if last_offset >= partition_stop:
        #        break
        #    recs.append(rec)
    return len(recs)


