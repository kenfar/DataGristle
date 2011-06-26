#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import fileinput
import collections
import optparse
import csv

#--- gristle modules -------------------
#import field_determinator as fielder


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

    def __init__(self, fqfn):
        """  fqfn = fully qualified file name
        """
        self.fqfn                 = fqfn
        self.has_header           = None
        self.format_type          = None
        self.fixed_length         = None
        self.field_cnt            = None
        self.record_cnt           = None
        self.csv_quoting          = None
        self.dialect              = None # python csv module variable

    def analyze_file(self):
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        self.format_type   = self._get_format_type()
        self.dialect       = self._get_dialect()
        self.has_header    = self._has_header()
        self.field_cnt     = self._get_field_cnt()
        self.record_cnt    = self._count_records()
        if QUOTE_DICT[self.dialect.quoting] == 'QUOTE_NONE':
            self.csv_quoting = False
        else:
            self.csv_quoting = True

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

    def _has_header(self):
        """ figure out whether or not there's a header based on the
            first 50,000 bytes
        """
        sample      = open(self.fqfn, 'r').read(50000)
        return csv.Sniffer().has_header(sample)
        
    def _get_field_cnt(self):
        """ determines the number of fields in the file.
 
            To do:  make it less naive - it currently assumes that all #recs
            will have the same number of fields.  It should be improved to 
            deal with bad data.
        """
        for row in csv.reader(open(self.fqfn,'r'), self.dialect):
            return len(row)
 
    def _get_format_type(self):
        """ Determines format type based on whether or not all records
            are of the same length.
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
        for rec in fileinput.input(self.fqfn):
            rec_cnt += 1
        return rec_cnt



