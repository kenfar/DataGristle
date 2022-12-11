#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
import os.path
from typing import Optional
from pprint import pprint as pp



class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - dialect
          - record_cnt
    """

    def __init__(self,
                 input_handler,
                 read_limit: int = -1) -> None:
        """
        Args:
            - input_handler:
            - read_limit: default is -1, which means unlimited
        """
        assert read_limit is not None
        self.input_handler = input_handler
        self.read_limit: int = read_limit

        self.dialect = self.input_handler.dialect
        self.field_cnt: int = 0
        self.record_cnt: int = 0
        self.record_cnt_is_est: bool = False


    def analyze_file(self) -> None:
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        self.record_cnt, self.record_cnt_is_est \
             = self.input_handler.get_rec_count(self.read_limit)
        self.field_cnt = self.input_handler.get_field_count()
        if self.input_handler.header:
            self.record_cnt += 1

        self.input_handler.reset()

        # I think we can get rid of this code - it sometimes has false positives
        # when it thinks a 1-record file is a header.  Leaving it out means that if
        # there's just a file then the field-level analysis is skimpy.  That's ok.
        # Research: impact on other programs! slicer?
        #if self.record_cnt == 1 and self.input_handler.dialect.has_header:
        #    raise IOErrorEmptyFile("Empty File")

        self.input_handler.close()


class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
