#!/usr/bin/env python
""" Extracts subsets of an input file based on user-specified criteria.

    Criteria is limited at this time to just a single column number,
    a simple operator and a literal value to compare to.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer

    To do:
    - add more sophisticated query language and parsing
    - address issue with comparisons to strings
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
#from pprint import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running from project structure
sys.path.append('../../')  # allows running from project test directory

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
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename,
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
                                       
    my_file.analyze_file()

    csvfile = open(my_file.fqfn, "r")
    for rec in csv.reader(csvfile, my_file.dialect):
        out_rec  = process_rec(rec, opts.criteria, opts.excriteria)
        if out_rec:
            write_fields(out_rec, my_file)
    csvfile.close()

    return 


def process_rec(rec, in_criteria, ex_criteria):
    """ Evaluates all the specifications against a record
        from the input file.
        Input:
            - rec:             used for rec specs
            - criteria:        filter criteria
        Output:
            - valid record
    """
    if not spec_evaluator(rec, in_criteria):
        return None
    elif spec_evaluator(rec, ex_criteria):
        return None

    return rec



def spec_evaluator(rec, spec):
    """ determines if record passes spec criteria
        Input:
           - rec (list of input fields)
           - spec (criteria)
        Output:
           - True or False
        To do:
           - Upgrade sophistication of selection criteria - consider
             using pyparsing, etc.
    """
    if spec:
        tokens = spec.split()
        assert(len(tokens) == 3)
        assert(tokens[1] in ['=','==','>','=>','>=','>','<','<=','=<','!='])
        assert(0 <= int(tokens[0]) < 200)
        query = "'%s' %s '%s'" % (rec[int(tokens[0])], tokens[1], tokens[2])
        if eval(query):
            return True
        else:
            return False
    else:
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
    use = ("%prog is used to extract rows that match filter criteria and write "
           "them out to stdout: \n"
           "\n"
           "   %prog -f [file] [misc options]"
           "\n")

    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', dest='filename', help='input file')

    parser.add_option('-c', '--criteria',
                      default=':',
                      help='inclusion criteria')
    parser.add_option('-C', '--excriteria',
                      help='exclusion criteria')
    parser.add_option('-d', '--delimiter',
                      help='Specify a quoted field delimiter.')
    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.')
    parser.add_option('--recdelimiter')

    (opts, args) = parser.parse_args()

    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

