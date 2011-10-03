#!/usr/bin/env python
""" Extracts subsets of input file based on user-specified columns and rows.
    The input file is assumed to be a csv file - as is the output printed 
    through stdout.

    The columns and rows are specified using python list slicing syntax -
    so individual columns or rows can be listed as can ranges.   Inclusion
    or exclusion logic can be used - and even combined.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
#from pprint import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running from project structure
sys.path.append('../../')  # allows running from project structure

import gristle.file_type           as file_type 

SMALL_SIDE = 0
LARGE_SIDE = 1

#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ runs all processes:
            - gets opts & args
            - analyzes file to determine csv characteristics
            - runs each input record through process_cols to get output
            - writes records
    """
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    my_file.analyze_file()

    rec_cnt = -1
    csvfile = open(my_file.fqfn, "r")
    for cols in csv.reader(csvfile, my_file.dialect):
        rec_cnt += 1
        new_cols = process_cols(rec_cnt, opts.records, opts.exrecords,
                                cols, opts.columns, opts.excolumns)
        if new_cols:
            write_fields(new_cols, my_file)
    csvfile.close()

    return 


def process_cols(rec_number,
                 incl_rec_spec, excl_rec_spec, 
                 cols, 
                 incl_col_spec, excl_col_spec):
    """ Evaluates all the specifications against a record
        from the input file.
        Input:
            - rec_number:      used for rec specs
            - incl_rec_spec
            - excl_rec_spec
            - cols:            a list of all columns from the record
            - incl_col_spec:   which columns to include
            - excl_col_spec:   which columns to exclude
        Output:
            - if the rec_number fails:  None
            - if the rec_number passes: a list of the columns that passed
    """

    #pp(locals())

    if not spec_evaluator(rec_number, incl_rec_spec):
        return None
    elif spec_evaluator(rec_number, excl_rec_spec):
        return None

    output_cols = []
    for col_number in range(len(cols)):
        if not spec_evaluator(col_number, incl_col_spec):
            continue
        if spec_evaluator(col_number, excl_col_spec):
            continue
        output_cols.append(cols[col_number])

    return output_cols


def spec_evaluator(value, spec_list):
    """ Evaluates a number against a list of specifications.
        Description:
            - uses the python string slicing formats to specify
              valid ranges (all offset from 0):
              - 4, 5, 9 = values 4, 5, and 9 
              - 1:3     = values 1 & 2 (end - 1)
              - 5:      = values 5 to the end 
              - :5      = values 0 to 4 (end - 1)
              - :       = all values
            - template:  spec, spec, spec:spec, spec, spec:spec
            - example:   4,    8   , 10:14    , 21  , 48:55
            - The above example is stored in a five-element spec-list
        Input:
            - value:  a column or record number
            - spec_list: a list, can be None
        Output:
            - True if the number matches one of the specs
            - False if the number does not match one of the specs
            - False if the spec_list is empty
        To do:
            - support slice steps
            - support negative numbers
    """
    if spec_list is None:
        return False

    int_value = int(value)
    for spec in spec_list:
        if ':' in spec:
 
            if spec == ':':                
                return True             
  
            spec_parts = spec.split(':')
            assert(len(spec_parts) <= 2)

            if spec.endswith(':'):          
                if int_value >= int(spec_parts[SMALL_SIDE]):
                    return True
            elif spec.startswith(':'):       
                if int_value < int(spec_parts[LARGE_SIDE]):
                    return True
            else:
                if (int(spec_parts[SMALL_SIDE]) 
                    <= int_value 
                    < int(spec_parts[LARGE_SIDE])):
                    return True
        elif int_value == int(spec):               
            return True

    return False
           


def write_fields(fields, my_file):
    """ Writes output to output destination.
        Input:
            - list of fields to write
            - output object
        Output:
            - delimited output record written to stdout
        To Do:
            - write to output file
    """
    rec = my_file.delimiter.join(fields)
    print rec


def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("%prog is used to extract column and row subsets out of "
           "files and write them out to stdout: \n" 
           " \n"
           "   %prog -f [file] [misc options]")
    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', dest='filename', help='input file')

    parser.add_option('-c', '--columns',
           default=':',
           help=('Specify the columns to include via a comma-separated list of '
                 'columns and colon-separated pairs of column start & '
                 'stop ranges. The default is to include all columns. '))
    parser.add_option('-C', '--excolumns',
           help=('Specify the columns to exclude via a comma-separated list of '
                 'columns and colon-separated pairs of column start & '
                 'stop ranges.  The default is to exclude nothing. '))
    parser.add_option('-r', '--records',
           default=':',
           help=('Specify the records to include via a comma-separated list of '
                 'record numbers and colon-separated pairs of record start & '
                 'stop ranges.  The default is to include all records. '))
    parser.add_option('-R', '--exrecords',
           help=('Specify the records to exclude via a comma-separated list of '
                 'record numbers and colon-separated pairs of record start & '
                 'stop ranges.  The default is to exclude nothing. '))
    parser.add_option('-d', '--delimiter',
           help=('Specify a quoted single-column field delimiter. This may be'
                 'determined automatically by the program. '))
    parser.add_option('--recdelimiter',
           help='Specify a quoted end-of-record delimiter. ')
    parser.add_option('--hasheader',
           default=False,
           action='store_true',
           help='Indicate that there is a header in the file.')

    (opts, args) = parser.parse_args()

    if opts.filename is None:
        parser.error("Error:  no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)


    def lister(arg_string):
        """ converts input commma-delimited string into a list
        """
        if arg_string:
            if ',' in arg_string:
                return arg_string.split(',')
            else:
                return [arg_string]
        else:
            return []

    opts.columns   = lister(opts.columns)
    opts.excolumns = lister(opts.excolumns)
    opts.records   = lister(opts.records)
    opts.exrecords = lister(opts.exrecords)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

