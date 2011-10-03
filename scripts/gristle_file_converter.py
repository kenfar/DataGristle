#!/usr/bin/env python
""" Converts file csv dialect - field delimiter and record delimiter.
    Also can be used to convert between multi-columna and single-column
    field delimiters.

    The input file is specified on the command line and the output is
    written to stdout.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
import fileinput
#import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running tests out of project structure

import gristle.file_type           as file_type 

#from pprint import pprint as pp
#pp(sys.path)


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Analyzes the file to automatically determine input file csv 
        characteristics.  Then reads one record at a time and writes it
        out.

        Note that it doesn't yet use the csv module (or an extended version)
        for multi-column delimited-files and doesn't use the csv module
        for writing the records.
    """
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    my_file.analyze_file()

    rec_cnt = -1
    if not my_file.delimiter or len(my_file.delimiter) == 1:
        csvfile = open(my_file.fqfn, "r")
        for fields in csv.reader(csvfile, my_file.dialect):
            rec_cnt += 1
            if my_file.has_header and rec_cnt == 0:
                continue
            write_fields(fields, my_file, opts.out_delimiter, 
                         opts.out_recdelimiter)
        csvfile.close()
    else:
        # csv module can't handle multi-column delimiters:
        for rec in fileinput.input(my_file.fqfn):
            rec_cnt += 1
            if opts.recdelimiter:
                clean_rec = rec[:-1].split(opts.recdelimiter)[0]
            else:
                clean_rec = rec[:-1]
            fields = clean_rec.split(my_file.delimiter)
            if my_file.has_header and rec_cnt == 0:
                continue
            write_fields(fields, my_file, opts.out_delimiter, 
                         opts.out_recdelimiter)
        fileinput.close()

    return 0     


def write_fields(fields, my_file, out_delimiter, out_rec_delimiter):
    """ Writes output to output destination.
        Input:
            - list of fields to write
            - output object
        Output:
            - delimited output record written to stdout
        To Do:
            - write to output file
    """
    if out_rec_delimiter is None:
        rec = out_delimiter.join(fields)
    else:
        rec = "%s%s" % (out_delimiter.join(fields), out_rec_delimiter)
    print rec


def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    
    use = ("%prog converts files between different CSV file formats. \n"
           "\n"
           "   %prog -f [file] [misc options]"
           "\n")

    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', 
           dest='filename', 
           help='input file')
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
    parser.add_option('-d', '--delimiter',
           help=('Specify a quoted field delimiter.'
                 'This is especially useful for multi-col delimiters.'))
    parser.add_option('-D', '--outdelimiter',
           dest='out_delimiter',
           help=('Specify a quoted field delimiter'
                 'This is especially useful for multi-col delimiters.'))
    parser.add_option('-r', '--recdelimiter',
           help='Specify a quoted end-of-record delimiter. ')
    parser.add_option('-R', '--outrecdelimiter',
           dest='out_recdelimiter',
           help='Specify a quoted end-of-record delimiter. ')
    parser.add_option('--hasheader',
           default=False,
           action='store_true',
           help='Indicates the existance of a header in the file.')
    parser.add_option('-H', '--outhasheader',
           default=False,
           action='store_true',
           dest='out_hasheader',
           help='Specify that a header within the input file will be retained')

    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

