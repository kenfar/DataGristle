#!/usr/bin/env python
""" Display data a single record of a file, one field per line, with
    field names displayed as labels to the left of the field values.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import linecache
import csv

#--- gristle modules -------------------
sys.path.append('../')  # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure

import gristle.file_type           as file_type 
import gristle.field_type          as typer
import gristle.field_determinator  as field_determinator


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Analyzes file then displays a single record
    """
    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.filename, opts.delimiter)
    MyFile.analyze_file()

    # Get Analysis on ALL Fields:
    MyFields = field_determinator.FieldDeterminator(opts.filename,
                                  MyFile.format_type,
                                  MyFile.field_cnt,
                                  MyFile.has_header,
                                  MyFile.dialect,
                                  opts.verbose)
    MyFields.analyze_fields()

    rec = get_rec(opts.filename, 
                  opts.recnum, 
                  MyFile.dialect)
    if rec is None:
       print 'No record found'
       return
    
    display_rec(rec, MyFile, MyFields)

    return 0     



def display_rec(rec, MyFile, MyFields):
    """ Displays a single record
     
        To do:
           - add simple navigation 
    """
    for sub in range(MyFile.field_cnt):
        #print '%-20s  -  %-40s' % (MyFields.field_names[sub][0], rec[sub])
        print '%-20s  -  %-40s' % (MyFields.field_names[sub], rec[sub])



def get_rec(filename, recnum, dialect):
    """ Gets a single record from a file
        Since it reads from the begining of the file it can take a while to get
        to records at the end of a large file
    """

    f = open(filename, 'rt')

    rec = None
    i   = 0
    try:
       reader = csv.reader(f, dialect)
       for row in reader:
           i += 1
           if i == recnum:
              rec = row 
              break
    finally:
       f.close()
    return rec




def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("The %prog is used to view data one record at a time. \n"
          + "   %prog -f [file] -q -v -h --delimiter [value] --recnum [value] \n")

    parser = optparse.OptionParser(usage = use)
    parser.add_option('-f', '--file', dest='filename', help='input file')
    parser.add_option('-q', '--quiet',
                      action='store_false',
                      dest='verbose',
                      default=False,
                      help='provides less detail')
    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      help='provides more detail')
    parser.add_option('-r', '--recnum',
                      default=1,
                      type=int,
                      help='display this record number, default to 1')
    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter - essential for multi-column delimiters.  Delimiter must be quoted.')


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

