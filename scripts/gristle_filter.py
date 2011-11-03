#!/usr/bin/env python
""" Extracts subsets of an input file based on user-specified criteria.

    Criteria is limited at this time to just a single column number,
    a simple operator and a literal value to compare to.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer

    To do:
    - add more sophisticated query language and parsing
    - address issue with comparisons to strings

    Usage examples:
       cat ../data/*crime* | ./gristle_filter.py -c "0 == Washington " -d ','
       cat ../data/*crime* | ./gristle_filter.py -c "0 == Washington " -d ','  -o /tmp/junk.dat
       ./gristle_filter.py -c "0 == Washington " -d ',' -f ../data/*crime*
"""

#--- standard modules ------------------
from __future__ import division
import sys
import optparse
import csv
import fileinput
#from pprint import as pp

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
            - analyzes file to determine csv characteristics for option files,
              uses options & defaults for stdin.
            - runs each input record through process_cols to get output
            - writes records to stdout or an option filename
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
        outfile = open(opts.output, 'w')
    else:
        outfile = sys.stdout

    for rec in csv.reader(fileinput.input(files), dialect):
        out_rec  = process_rec(rec, opts.criteria, opts.excriteria)
        if out_rec:
            write_fields(out_rec, outfile, dialect.delimiter)
    fileinput.close()

    if opts.output:
        outfile.close()

    return 0


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
        query = "'%s' %s '%s'" % (rec[int(tokens[0])].strip(), tokens[1], tokens[2])
        if eval(query):
            return True
        else:
            return False
    else:
        return False
 


def write_fields(fields, outfile, delimiter):
    """ Writes output to output destination.
        Input:
            - list of fields to write
            - output object
        Output:
            - delimited output record written to stdout
    """

    rec = delimiter.join(fields)
    outfile.write(rec + '\n')


def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - files list
    """
    use = ("%prog is used to extract rows that match filter criteria and write "
           "them out to stdout: \n"
           "\n"
           "   %prog [file] [misc options]"
           "\n")

    parser = optparse.OptionParser(usage = use)

    parser.add_option('-o', '--output', 
           help='Specifies the output file.  The default is stdout.  Note that'
                'if a filename is provided the program will override any '
                'file of that name.')
    parser.add_option('-c', '--criteria',
           default=':',
           help='inclusion criteria')
    parser.add_option('-C', '--excriteria',
           help='exclusion criteria')
    parser.add_option('-d', '--delimiter',
           help=('Specify a quoted single-column field delimiter. This may be'
                 'determined automatically by the program - unless you pipe the'
                 'data in.'))
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
           help='indicates that there is a header in the file.')
    parser.add_option('--recdelimiter')

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

