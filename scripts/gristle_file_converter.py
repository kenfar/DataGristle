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
import pprint as pp

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
    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    MyFile.analyze_file()

    rec_cnt = -1
    if not MyFile.delimiter or len(MyFile.delimiter) == 1:
        csvfile = open(MyFile.fqfn, "r")
        for fields in csv.reader(csvfile, MyFile.dialect):
            rec_cnt += 1
            if MyFile.has_header and rec_cnt == 0:
                continue
            write_fields(fields, MyFile, opts.out_delimiter, opts.out_recdelimiter)
        csvfile.close()
    else:
        # csv module can't handle multi-column delimiters:
        for rec in fileinput.input(MyFile.fqfn):
            rec_cnt += 1
            if opts.recdelimiter:
                 clean_rec = rec[:-1].split(opts.recdelimiter)[0]
            else:
                 clean_rec = rec[:-1]
            fields = clean_rec.split(MyFile.delimiter)
            if MyFile.has_header and rec_cnt == 0:
                continue
            write_fields(fields, MyFile, opts.out_delimiter, opts.out_recdelimiter)
        fileinput.close()

    return 0     


def process_fields(fields, columns):

    output_fields = []
    for col in columns:
        output_fields.append(fields[col])
    return output_fields


def write_fields(fields, MyFile, out_delimiter, out_rec_delimiter):
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
    
    use = "Usage: %prog -f [file] -q -v --delimiter [quoted delimiter] --outdelimiter [quoted delimiter] --hasheader"
    use = ("The %prog is used to convert files between different CSV file formats. \n"
          + "   %prog -f [file] -q -v -h --delimiter [value] --outdelimiter [value] \n"
          + "        --recdelimiter [value] --outrecdelimiter [value] --hasheader --outhasheader --hasheader --help")

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

    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter - essential for multi-column delimiters.  Delimiter must be quoted.')
    parser.add_option('-D', '--outdelimiter',
                      dest='out_delimiter',
                      help='specify a field delimiter - essential for multi-column delimiters.  Delimiter must be quoted.')

    parser.add_option('-r', '--recdelimiter',
                      help='specify an end-of-record delimiter.  The deimiter must be quoted.')
    parser.add_option('-R', '--outrecdelimiter',
                      dest='out_recdelimiter',
                      help='specify an end-of-record delimiter.  The deimiter must be quoted.')

    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.  Essential for multi-column delimited files.')
    parser.add_option('-H', '--outhasheader',
                      default=False,
                      action='store_true',
                      dest='out_hasheader',
                      help='indicates that there is a header in the file.  Essential for multi-column delimited files.')


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

