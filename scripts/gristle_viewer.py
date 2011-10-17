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
import csv
from pprint import pprint as pp


#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure

import gristle.file_type           as file_type 
import gristle.field_determinator  as field_determinator


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Analyzes file then displays a single record
    """
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename, opts.delimiter)
    my_file.analyze_file()

    # Get Analysis on ALL Fields:
    my_fields = field_determinator.FieldDeterminator(opts.filename,
                                  my_file.format_type,
                                  my_file.field_cnt,
                                  my_file.has_header,
                                  my_file.dialect,
                                  opts.verbose)
    my_fields.analyze_fields()

    rec = get_rec(opts.filename, 
                  opts.recnum, 
                  my_file.dialect)
    if rec is None:
        print 'No record found'
        return
    
    display_rec(rec, my_file, my_fields)

    return 0     



def display_rec(rec, my_file, my_fields):
    """ Displays a single record
     
        To do:
           - add simple navigation 
    """

    # figure out label length for formatting:
    max_v_len = 0
    for v in my_fields.field_names.values():
       if len(v) > max_v_len:
           max_v_len = len(v)
    min_format_len  =  max_v_len + 4

    # print in column order:
    for sub in range(my_file.field_cnt):
        print '%-*s  -  %-40s' % (min_format_len, my_fields.field_names[sub], rec[sub])



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
            if i == recnum:
                rec = row 
                break
            else:
                i += 1
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
           "   %prog -f [file] -q -v -h --delimiter [value] "
           "--recnum [value] \n")

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
                      help='display this record number, start at 0, default to 1')
    parser.add_option('-d', '--delimiter',
                      help=('Specify a quoted field delimiter -'
                            ' esp. for multi-col delimiters.'))


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

