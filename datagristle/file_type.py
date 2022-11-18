#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
import csv
import fileinput
import os
import os.path
from pprint import pprint
from typing import Optional, Tuple
from pprint import pprint as pp

import datagristle.csvhelper as csvhelper



class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - dialect
          - record_cnt
    """

    def __init__(self,
                 dialect: csvhelper.Dialect,
                 fqfn: str,
                 read_limit: int = -1) -> None:
        """
        Arguments:
            - dialect = a csv dialect - should be valid, not empty
            - fqfn = fully qualified file name
            - read_limit = default is -1, which means unlimited
        """
        assert read_limit is not None
        self.dialect = dialect
        self.fqfn = fqfn
        self.field_cnt: Optional[int] = None
        self.record_cnt: Optional[int] = None
        self.record_cnt_is_est: Optional[bool] = None
        self.read_limit: int = read_limit


    def analyze_file(self) -> None:
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        if os.path.getsize(self.fqfn) == 0:
            raise IOErrorEmptyFile("Empty File")

        self.record_cnt, self.record_cnt_is_est = self._count_records()
        self.field_cnt = get_field_cnt(self.dialect, self.fqfn)

        if self.record_cnt == 1 and self.dialect.has_header:
            raise IOErrorEmptyFile("Empty File")


    def _count_records(self) -> Tuple[int, bool]:
        """ Returns the number of records in the file
            Outputs:
               - rec count
               - estimated - True or False, indicates if the rec count is an
                 estimation based on the first self.read_limit rows.
        """
        rec_cnt = 0
        estimated_rec_cnt = 0
        byte_cnt = 0
        estimated = True if self.read_limit > -1 else False

        if estimated:
            # fastest method, should be helpful if the read_limit is very high
            # but can miscount rows if newlines are in a field
            estimated = True
            infile = open(self.fqfn, 'rt')
            for rec in infile:
                byte_cnt += len(rec)
                rec_cnt += 1
                if rec_cnt >= self.read_limit:
                    break
            infile.close()
            try:
                bytes_per_rec = byte_cnt / rec_cnt
                estimated_rec_cnt = int(os.path.getsize(self.fqfn) / bytes_per_rec)
            except  ZeroDivisionError:
                pass

        else:
            # much slower method, but most accurate
            with open(self.fqfn, 'rt') as infile:
                reader = csv.reader(infile, self.dialect)
                for _ in reader:
                    rec_cnt += 1

        return estimated_rec_cnt or rec_cnt, estimated



def get_field_cnt(dialect: csvhelper.Dialect,
                  fqfn: str) -> Optional[int]:
    """ determines the number of fields in the file.
    """
    field_cnt = None
    for rec in csv.reader(fileinput.input(fqfn), dialect):
        field_cnt = len(rec)
        break
    fileinput.close()

    return field_cnt



class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass
