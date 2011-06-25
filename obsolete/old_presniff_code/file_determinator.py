#!/usr/bin/env python
""" determinator:  used to identify characteristics of a file
    
    todo:
      - get field names
      - get field types
      - get min & max values
      - get mean
      - 
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""
import sys
import os
import fileinput
import collections
import optparse
import csv


#------------------------------------------------------------------------------
# file determination section
#------------------------------------------------------------------------------
class FileTyper(object):

    def __init__(self, fqfn, confidence_level=9):
         """  fqfn = fully qualified file name
         """
         self.fqfn                 = fqfn
         self.confidence_level     = confidence_level
         self.format_type          = None
         self.csv_field_delimiter  = None
         self.csv_record_delimiter = None
         self.csv_quoting          = None
         self.fixed_length         = None
         self.field_number         = None
         self.record_number        = None
         self.dialect              = None # python csv module variable
         self.fields               = {}


    def analyze_file(self):
        """ analyzes a file to determine the following:
            - format type     
            - csv_field_delimiter
            - csv_record_delimiter
            - csv_quoting
        """
        self.format_type = self._get_format_type(self.fqfn)

        self.csv_field_delimiter = self._get_field_delimiter(self.fqfn)

        self.field_number = self._get_field_number(self.fqfn, 
                                                   self.csv_field_delimiter)

        self.csv_quoting  = self._get_csv_quoting(self.fqfn,
                                                  self.csv_field_delimiter)

        self.record_number = self._get_record_number(self.fqfn)

     
        self.dialect       = self._get_dialect(self.fqfn)


    def _get_dialect(self, fqfn):
        """ printlines from http://www.doughellmann.com/PyMOTW/csv/
        """
        csvfile = open(fqfn, "rb")
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.close()
        print csv.list_dialects()

        print 
        print '  delimiter        = %-6r   ' % dialect.delimiter
        print '  skipinitialspace = %r'      % dialect.skipinitialspace
        print '  doublequote      = %-6r  '  % dialect.doublequote
        print '  quotechar        = %-6r  '  % dialect.quotechar
        print '  lineterminator   = %r'      % dialect.lineterminator
        print '  escapechar       = %-6r'    % dialect.escapechar
        print

        return dialect


    def _get_record_number(self, fqfn):
        record_number = 0
        for rec in fileinput.input(fqfn):
            record_number += 1
        return record_number


    def _get_csv_quoting(self, fqfn, delimiter):
        quoting            = False
        quoted_fields      = collections.defaultdict(int)
        record_number      = 0

        for rec in fileinput.input(fqfn):
            record_number += 1
            fields = rec[:-1].split(delimiter)
            for i in range(len(fields)):
                if fields[i][0]    == '"' \
                and fields[i][-1:] == '"':
                    quoted_fields[i] += 1

        for key in quoted_fields:
            if quoted_fields[key] == record_number:
               quoting = True

        return quoting
  


    def _get_field_number(self, fqfn, delimiter):
        """ Given a file name and a delimiter - this function will determine
            the number of fields in the file.

            Returns number of fields or None if uncertain.

            To do:  make it less naive - it currently assumes that all recs
            will have the same number of fields.  It should be improved to 
            dealth with delimiters within quoted strings, escaped delimiters,
            and bad data.
        """
        field_length = collections.defaultdict(int)
        for rec in fileinput.input(fqfn):
            fields = rec.split(delimiter)
            curr_field_number = len(fields)
            field_length[len(fields)] += 1
     

        if len(field_length) == 1:
            return field_length.keys()[0]    # just one entry
        else:
            return None                      # uncertain of delimiter


    def _get_format_type(self, fqfn):
        """ 
        """
        rec_length = collections.defaultdict(int)
        for rec in fileinput.input(fqfn):
            rec_length[len(rec)] += 1
        
        if len(rec_length) == 1:
           return 'fixed'
        else:
           return 'csv'


    def _get_field_delimiter(self, fqfn):
        """ The purpose is to determine fhe field delimiter of the csv file
            Returns the delimiter value.
            To do:
              1. integrate both primary loops so that it can only process
                 as much data as is necessary
        """     
        delimiter  = None

        # first build a dict of dicts to track frequency distrib
        # of chars within each record
        records       = {}  
        rec_number    = 0
        odd_char_list = ['"']

        for rec in fileinput.input(fqfn):
            rec_number += 1
            chars       = collections.defaultdict(int)

            for char in rec[:-1]:
                if char not in odd_char_list:
                   chars[char] += 1

            records[rec_number] = chars

        # next build a dict of char frequencies across all records
        non_delimiters = []
        delimiters     = []
        for record in records:
            for char in records[record]:
                if char in non_delimiters:
                   pass
                elif char in delimiters:
                   pass
                else:
                   if self._is_delimiter(char, records, delimiters, 
                      non_delimiters):
                      delimiters.append(char)
                   else:
                      non_delimiters.append(char)

        # next return discovered delimiter
        # need better code in case of 0 consistent delimiters or more than 1
        if len(delimiters) == 1:
           return delimiters[0]
        else:
           print "more than 1 delimiter possibility found: "
           print delimiters
           return None
 
                
    def _is_delimiter(self, char, records, delimiters, non_delimiters):
  
       # create a dictionary with all frequencies of occurances across recs
       # key   = number of occurances within a record
       # value = number of records this happens on
       rec_freq = collections.defaultdict(int)
       for record in records:
           rec_freq[records[record][char]] += 1

       if len(rec_freq) == 1:
          return True
       else:
          return False




#------------------------------------------------------------------------------
# field determination section
#------------------------------------------------------------------------------
class FieldTyper(object):

    def __init__(self, 
                 filename, 
                 format_type, 
                 field_number,
                 csv_field_delimiter,
                 csv_quoting):
        self.filename            = filename
        self.format_type         = format_type
        self.field_number        = field_number
        self.csv_field_delimiter = csv_field_delimiter
        self.csv_quoting         = csv_quoting
        self.fields              = []

 
    def analyze_fields(self):

        self.fields = self._get_field_names(self.filename, 
                                            self.format_type,
                                            self.field_number,
                                            self.csv_field_delimiter,
                                            self.csv_quoting)

    def _get_field_names(self, 
                         filename, 
                         format_type, 
                         field_number,
                         field_delimiter, 
                         quoting):
        
        # first determine if the types of the first rec are different 
        type_test = self._header_test_by_type(filename, field_delimiter)
            

        fields = []
        return fields


    def _header_test_by_type(self, filename, field_delimiter):
        """ Determines if the first row is a header by seeing if there's a
            single field with all non-character values.  Assumes that a header
            be have at least 1 character value
        """
        MyCSV = csv.reader(open(filename, 'rb'), delimiter=field_delimiter)
        print MyCSV.next()
        for row in MyCSV:
            print row
        return True




    def _get_field_types(self, filename, format_type, field_delimiter, quoting):
        pass

  

#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Allows users to directly call file_determinator() from command line
    """
    (opts, args) = get_args()
    MyFile = FileTyper(opts.filename)
    MyFile.analyze_file()

    print '   format type:      %s' % MyFile.format_type
    print '   field delimiter:  %s' % MyFile.csv_field_delimiter
    print '   field_number:     %d' % MyFile.field_number
    print '   csv quoting:      %s' % MyFile.csv_quoting
    print '   record number:    %d' % MyFile.record_number
    
    MyFields = FieldTyper(opts.filename,
                          MyFile.format_type,
                          MyFile.field_number,
                          MyFile.csv_field_delimiter,
                          MyFile.csv_quoting)
    MyFields.analyze_fields()
    

def get_args():
    """
    """
    # get args
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename",help="input file")
    (opts, args) = parser.parse_args()

    # validate args
    if opts.filename is None:
       parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
       parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
   main()

