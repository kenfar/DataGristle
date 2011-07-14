#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - main function
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
    MyFile       = file_type.FileTyper(opts.filename)
    MyFile.analyze_file()

    # Get Analysis on ALL Fields:
    MyFields = field_determinator.FieldDeterminator(opts.filename,
                                  MyFile.format_type,
                                  MyFile.field_cnt,
                                  MyFile.has_header,
                                  MyFile.dialect)
    MyFields.analyze_fields()

    
    display_rec(opts.filename, opts.recnum, MyFile, MyFields)

    return 0     



def display_rec(filename, recnum, MyFile, MyFields):

    print

    rec = get_rec(filename, recnum)
    if rec is None:
       print 'No record found'
       return

    print rec

    for sub in range(MyFile.field_cnt):
        print '%s:   %s' % (MyFields.field_names[sub], rec[sub])

    


def get_rec(filename, recnum):

    f = open(filename, 'rt')
    i = 0
    rec = None
    try:
       reader = csv.reader(f)
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
    use = "Usage: %prog -f [file] -q -v -r [record-number]"
    parser = optparse.OptionParser(usage = use)
    parser.add_option('-f', '--file', dest='filename', help='input file')
    parser.add_option('-q', '--quiet',
                      action='store_false',
                      dest='verbose',
                      default=True,
                      help='provides less detail')
    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      default=True,
                      help='provides more detail')
    parser.add_option('-r', '--recnum',
                      default=0,
                      type=int,
                      help='display this record number')

    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

