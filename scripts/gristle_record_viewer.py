#!/usr/bin/env python
""" Used to display a single record of a file, one field per line, with
    field names displayed as labels to the left of the field values.

    contains:
      - main function
      - get_rec
      - display_rec
      - get_opts_and_args function

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

import gristle.file_type           as file_type 
import gristle.field_type          as typer
import gristle.field_determinator  as field_determinator


QUOTE_DICT = {}
QUOTE_DICT[0] = 'QUOTE_MINIMAL'
QUOTE_DICT[1] = 'QUOTE_ALL'
QUOTE_DICT[2] = 'QUOTE_NONNUMERIC'
QUOTE_DICT[3] = 'QUOTE_NONE'



#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ 
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

    print

    for sub in range(MyFile.field_cnt):
        print '%-20s   %-40s' % (MyFields.field_names[sub], rec[sub])



def get_rec(filename, recnum, dialect):

    f = open(filename, 'rt')

    rec = None
    i   = 0
    try:
       reader = csv.reader(f, dialect)
       for row in reader:
           i += 1
           if i == recnum:
              rec = row 
    finally:
       f.close()
    return rec




def get_opts_and_args():
    """ gets opts & args and returns them
        run program with -h or --help for command line args
    """
    # get args
    use = "Usage: %prog -f [file] -q -v -r [record-number] -d [delimiter]"
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
    parser.add_option('-s', '--silent',
                      action='store_true',
                      dest='silent',
                      default=False,
                      help='performs operation with no output')
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

    if opts.silent:
        opts.verbose = False

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

