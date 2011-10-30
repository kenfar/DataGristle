#!/usr/bin/env python
""" Display data a single record of a file, one field per line, with
    field names displayed as labels to the left of the field values.

    Also allows simple navigation between records.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer

    To do:
       1.  check for recnum > number of records in input file
       2.  consider adding records up to some threshold to dictionary
           to allow navigation for stdin data & faster for files
       3.  confirm that record counting works identical for each situation
       4.  use header info when using stdin
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
import fileinput
from pprint import pprint as pp


#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure

import gristle.file_type           as file_type 
import gristle.field_determinator  as field_determinator
import gristle.field_type          as field_type


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Analyzes file then displays a single record and allows simple 
        navigation between records.
    """
    (opts, files) = get_opts_and_args()

    if len(files) == 1:
        my_file                = file_type.FileTyper(files[0], opts.delimiter)
        my_file.analyze_file()
        my_fields              = field_determinator.FieldDeterminator(files[0],
                                      my_file.format_type,
                                      my_file.field_cnt,
                                      my_file.has_header,
                                      my_file.dialect,
                                      opts.verbose)
        my_fields.analyze_fields()
        dialect                = my_file.dialect
    else:
        # Dialect parameters needed for stdin - since the normal code can't
        # analyze this data & guess the csv properties.
        my_fields              = None
        dialect                = csv.Dialect
        dialect.delimiter      = opts.delimiter
        dialect.quoting        = opts.quoting
        dialect.quotechar      = opts.quotechar
        dialect.lineterminator = '\n'                 # naive assumption

    while True:
       rec = get_rec(files, 
                     opts.recnum, 
                     dialect)
       if rec is None:
           print 'No record found'
           return
    
       display_rec(rec, my_fields, opts.output)

       # Need to end here if data came from stdin:
       if not files:
           break

       # Need to end here if data is being directed to a file - and not interactive
       if opts.output:
           break
 
       response = raw_input('Rec: %d     Q[uit] P[rev] N[ext] T[op], or a specific record number: ' % opts.recnum).lower()
       if response == 'q':
           break
       elif response == 'p':
           opts.recnum -= 1
       elif response == 'n':
           opts.recnum += 1
       elif response == 't':
           opts.recnum = 0
       elif field_type._get_type(response) == 'integer':
           opts.recnum = int(response)
       else:
           print 'Invalid response, please enter q, p, n, t, or a specific record number'
       
       print response

    return 0     



def display_rec(rec, my_fields, outfile_name):
    """ Displays a single record
    """

    # figure out label length for formatting:
    field_names = []
    if my_fields:
        max_v_len = 0
        for v in my_fields.field_names.values():
           if len(v) > max_v_len:
               max_v_len = len(v)
        min_format_len  =  max_v_len + 4
        field_names = my_fields.field_names
    else:
        for sub in range(len(rec)):
            field_names.append('field_%d' % sub)        
        min_format_len = 12

    if outfile_name:
        outfile = open(outfile_name, 'w')
    else:
        outfile = sys.stdout
    
    # write in column order:
    for sub in range(len(rec)):
        outfile.write('%-*s  -  %-40s\n' % (min_format_len, field_names[sub], rec[sub]))

    # don't close stdout
    if outfile_name:
        outfile.close()



def get_rec(files, recnum, dialect):
    """ Gets a single record from a file
        Since it reads from the begining of the file it can take a while to get
        to records at the end of a large file

        To do:
           - possibly keep file open in case user wants to navigate about
           - possibly keep some of the data in a dictionary in case the user
             wants to navigate about
    """

    found = None
    i     = 0
    for row in csv.reader(fileinput.input(files), dialect): 
        if i == recnum:
            found = row
            break
        else:
            i += 1
    fileinput.close()

    return found





def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("The %prog is used to view data one record at a time. \n"
           "   %prog  [file] -q -v -h --delimiter [value] "
           "--recnum [value] \n")

    parser = optparse.OptionParser(usage = use)
    parser.add_option('-o', '--output', 
           help='Specifies the output file, defaults to stdout.')
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
           help='Specify a quoted field delimiter. ')
    parser.add_option('--quoting',
           default=False,
           help='Specify field quoting - generally only used for stdin data.'
                '  The default is False.')
    parser.add_option('--quotechar',
           default='"',
           help='Specify field quoting character - generally only used for '
                'stdin data.  Default is double-quote')

    (opts, files) = parser.parse_args()

    if files:
       if len(files) > 1 and not opts.delimiter:
           parser.error('Please provide delimiter when piping data into program via stdin or reading multiple input files')
    else:   # stdin
       if not opts.delimiter:
           parser.error('Please provide delimiter when piping data into program via stdin or reading multiple input files')


    return opts, files



if __name__ == '__main__':
    sys.exit(main())

