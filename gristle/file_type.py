#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

from __future__ import division

#--- standard modules ------------------
import fileinput
import collections
import csv
import os


QUOTE_DICT = {}
QUOTE_DICT[0] = 'QUOTE_MINIMAL'
QUOTE_DICT[1] = 'QUOTE_ALL'
QUOTE_DICT[2] = 'QUOTE_NONNUMERIC'
QUOTE_DICT[3] = 'QUOTE_NONE'



#------------------------------------------------------------------------------
# file determination section
#------------------------------------------------------------------------------
class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - csv_quoting
          - dialect
          - record_cnt
          - has_header
    """

    def __init__(self, fqfn, 
                 delimiter=None, rec_delimiter=None, has_header=None):
        """  fqfn = fully qualified file name
        """
        self.fqfn                 = fqfn
        self.delimiter            = delimiter
        self.rec_delimiter        = rec_delimiter
        self.has_header           = has_header
        self.format_type          = None
        self.fixed_length         = None
        self.field_cnt            = None
        self.record_cnt           = None
        self.csv_quoting          = None
        self.dialect              = None

    def analyze_file(self):
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        if os.path.getsize(self.fqfn) == 0:
            raise(IOErrorEmptyFile, "Empty File")
           
        if self.delimiter:                                 #delimiter overridden
            self.dialect                  = csv.Dialect
            self.dialect.delimiter        = self.delimiter
            self.dialect.skipinitialspace = False
            self.dialect.quoting          = True            #naive default!
            self.dialect.quotechar        = '"'             #naive default!
            self.dialect.lineterminator   = '\n'            #naive default!
        else:
            self.dialect                  = self._get_dialect()
            self.delimiter                = self.dialect.delimiter
            if QUOTE_DICT[self.dialect.quoting] == 'QUOTE_NONE':
                self.csv_quoting = False  # almost never see this value
            else:
                self.csv_quoting = True

        self.format_type         = self._get_format_type()
        self.dialect.has_header  = self._has_header(self.has_header)
        self.has_header          = self.dialect.has_header  # should eliminate
        self.field_cnt           = self._get_field_cnt()
        self.record_cnt          = self._count_records()


    def _get_dialect(self):
        """ gets the dialect for a file
        """
        csvfile = open(self.fqfn, "rb")
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(50000))
        except:
            print 'ERROR: Could not analyze file!'
            raise
        csvfile.close()
        return dialect


    def _has_header(self, has_header):
        """ if the has_header flag was already provided, then just return it
            back.
            Otherwise, figure out whether or not there's a header based on 
            the first 50,000 bytes
        """
        if has_header:
            return has_header
        else:
            sample      = open(self.fqfn, 'r').read(50000)
            return csv.Sniffer().has_header(sample)
        

    def _get_field_cnt(self):
        """ determines the number of fields in the file.
  
            To do:  make it less naive - it currently assumes that all #recs
            will have the same number of fields.  It should be improved to 
            deal with bad data.
        """
        if not self.delimiter or len(self.delimiter) == 1:
            csvfile = open(self.fqfn, "r")
            for row in csv.reader(csvfile, self.dialect):
                row_len = len(row)
                csvfile.close()
                break
        else:
            # csv module can't handle multi-column delimiters:
            for rec in fileinput.input(self.fqfn):
                fields = rec[:-1].split(self.delimiter)
                fileinput.close()
                row_len = len(fields)
                break

        return row_len
 

    def _get_format_type(self):
        """ Determines format type based on whether or not all records
            are of the same length.

            Returns either 'csv' or 'fixed'
        """
        rec_length = collections.defaultdict(int)
        rec_cnt = 0
        for rec in fileinput.input(self.fqfn):
            rec_length[len(rec)] += 1
            rec_cnt += 1
            if rec_cnt > 1000:     # don't want to read millions of recs
                break
        fileinput.close()
       
        if len(rec_length) == 1:
            return 'fixed'
        else:
            return 'csv'


    def _count_records(self):
        """ Returns the number of records in the file
        """
        rec_cnt = 0
        for dummy in fileinput.input(self.fqfn):
            rec_cnt += 1
        fileinput.close()
        return rec_cnt



class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass
