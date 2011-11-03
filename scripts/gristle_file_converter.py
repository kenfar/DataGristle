#!/usr/bin/env python
""" Converts file csv dialect - field delimiter and record delimiter.
    Also can be used to convert between multi-columna and single-column
    field delimiters.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer

    Example Usage:
    $ cat ../data/*crime* | ./gristle_file_converter.py -d ',' -D '|'  
"""

#--- standard modules ------------------
from __future__ import division
import sys
import optparse
import csv
import fileinput
#import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running tests out of project structure

import gristle.file_type           as file_type 


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
    (opts, files) = get_opts_and_args()

    if len(files) == 1:
        my_file       = file_type.FileTyper(files[0],
                                           opts.delimiter,
                                           opts.recdelimiter,
                                           opts.hasheader)
        try:
            my_file.analyze_file()
        except file_type.IOErrorEmptyFile:
            return 1

        dialect       = my_file.dialect
    else:
        # dialect parameters needed for stdin - since the normal code can't
        # analyze this data.
        dialect                = csv.Dialect
        dialect.delimiter      = opts.delimiter
        dialect.quoting        = opts.quoting
        dialect.quotechar      = opts.quotechar
        dialect.lineterminator = '\n'                 # naive assumption

    if opts.output:
        outfile  = open(opts.output, 'w')
    else:
        outfile  = sys.stdout

    rec_cnt = -1
    if (not dialect.delimiter
    or len(dialect.delimiter) == 1):
        for fields in csv.reader(fileinput.input(files), dialect):
            rec_cnt += 1
            #if my_file.has_header and rec_cnt == 0:   # need to review what to do with this
            #    continue
            write_fields(fields, opts.out_delimiter, 
                         opts.out_recdelimiter, outfile)        # replace my_file with what?
    else:
        # csv module can't handle multi-column delimiters:
        for rec in fileinput.input(files):
            rec_cnt += 1
            if opts.recdelimiter:
                clean_rec = rec[:-1].split(opts.recdelimiter)[0]
            else:
                clean_rec = rec[:-1]
            fields = clean_rec.split(dialect.delimiter)
            #if my_file.has_header and rec_cnt == 0:              # replace my_file with what?
            #    continue
            write_fields(fields, opts.out_delimiter, 
                         opts.out_recdelimiter, outfile)         # replace my_file with what?

    fileinput.close()
    if opts.output:
        outfile.close()

    return 0     


def write_fields(fields, out_delimiter, out_rec_delimiter, outfile):
    """ Writes output to output destination.
        Input:
            - list of fields to write
            - output object
        Output:
            - delimited output record written 
    """
    if out_rec_delimiter is None:
        rec = out_delimiter.join(fields)
    else:
        rec = "%s%s" % (out_delimiter.join(fields), out_rec_delimiter)
    outfile.write('%s\n'% rec)


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
           "   %prog [file] [misc options]"
           "\n")

    parser = optparse.OptionParser(usage = use)

    parser.add_option('-o', '--output', 
           help='Specifies output file. Default is stdout.')
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
    parser.add_option('--quoting',
           default=False,
           help='Specify field quoting - generally only used for stdin data.'
                '  The default is False.')
    parser.add_option('--quotechar',
           default='"',
           help='Specify field quoting character - generally only used for '
                'stdin data.  Default is double-quote')
    parser.add_option('--hasheader',
           default=False,
           action='store_true',
           help='Indicates the existance of a header in the file.')
    parser.add_option('-H', '--outhasheader',
           default=False,
           action='store_true',
           dest='out_hasheader',
           help='Specify that a header within the input file will be retained')

    (opts, files) = parser.parse_args()

    # validate opts
    if files:
        if len(files) > 1 and not opts.delimiter:
            parser.error('Please provide delimiter when piping data into program via stdin or reading multiple input files')
    else:   # stdin
        if not opts.delimiter:
            parser.error('Please provide delimiter when piping data into program via stdin or reading multiple input files')


    return opts, files



if __name__ == '__main__':
    sys.exit(main())

