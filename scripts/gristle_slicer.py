#!/usr/bin/env python
""" Prints subsets of a file based on user-specified columns and rows.

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
sys.path.append('../')  # allows running out of project structure

import gristle.file_type           as file_type 


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
    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    MyFile.analyze_file()

    rec_cnt = -1
    csvfile = open(MyFile.fqfn, "r")
    for cols in csv.reader(csvfile, MyFile.dialect):
        rec_cnt += 1
        new_cols = process_cols(rec_cnt, opts.records, opts.exrecords,
                                cols, opts.columns, opts.excolumns)
        if new_cols:
            write_fields(new_cols, MyFile)
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
            - template:  spec, spec, spec:spec, spec, spec_spec
            - example:   4,    8,  , 10:14    , 21  , 48:55
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

    SMALL_SIDE = 0
    LARGE_SIDE = 1

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
                if int(spec_parts[SMALL_SIDE]) <= int_value < int(spec_parts[LARGE_SIDE]):
                   return True
        elif int_value == int(spec):               
            return True

    return False
           


def write_fields(fields, MyFile):
    rec = MyFile.delimiter.join(fields)
    print rec


def get_opts_and_args():
    """ gets opts & args and returns them
        run program with -h or --help for command line args
    """
    # get args
    use = "Usage: %prog -f [file] -c [included columns] -C [excluded columns] -r [included records] -R [excluded records] --delimiter [quoted delimiter] --recdelimiter [quoted record delimiter] --hasheader"
    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', dest='filename', help='input file')

    parser.add_option('-c', '--columns',
                      default=':',
                      help='comma-separated list of column numbers to include')
    parser.add_option('-C', '--excolumns',
                      help='comma-separated list of column numbers to exclude')
    parser.add_option('-r', '--records',
                      default=':',
                      help='comma-separated list of record numbers to include')
    parser.add_option('-R', '--exrecords',
                      help='comma-separated list of record numbers to exclude')

    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter.  Delimiter must be quoted.')
    parser.add_option('--recdelimiter',
                      help='specify an end-of-record delimiter.  The deimiter must be quoted.')
    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.')

    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("Error:  no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)


    def lister(arg_string):
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

