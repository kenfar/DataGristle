#!/usr/bin/env python
""" Creates a frequency distribution of values from a single column of the
    input file and prints this out in descending order.
   
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
import collections
import operator

#--- gristle modules -------------------
sys.path.append('../')  # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure

import gristle.file_type           as file_type 


#from pprint import pprint as pp
#pp(sys.path)


def main():
    """ Runs analyzer to automatically determine file format
        Then accumulates the frequency distribution for the requested column
        Then sorts the distribution by value
        Then prints it
    """
    field_freq = collections.defaultdict(int)

    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    my_file.analyze_file()


    csvfile = open(my_file.fqfn, "r")
    for fields in csv.reader(csvfile, my_file.dialect):
        try:
            field_freq[fields[opts.column_number]] += 1
        except IndexError:
            continue   # skip short, bad, record
        if len(field_freq) > 50000:
            print 'Number of unique values exceeds limits - will truncate'
            break
    csvfile.close()

    sort_freq = sorted(field_freq.iteritems(), 
                       key=operator.itemgetter(1),
                       reverse=True)

    write_freq(sort_freq)

    return 0     


def write_freq(freq_list):
    """ Writes output to output destination.
        Input:
            - frequency distribution
        Output:
            - delimited output record written to stdout
        To Do:
            - write to output file
    """
    key = 0
    value = 1
    for freq_tup in freq_list:
        print "%s    -    %d" % (freq_tup[key], freq_tup[value])


def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("%prog is used to print a frequency distribution of a single column"
           " from the input file: \n"
           "\n"
           "   %prog -f [file] [misc options] "
           "\n")
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

    parser.add_option('-c', '--column',
                      type=int,
                      dest='column_number',
                      help='column number to analyze')

    parser.add_option('-d', '--delimiter',
                      help='Specify quoted field delimiter.')
    parser.add_option('--recdelimiter',
                      help='Specify quoted end-of-record delimiter.')
    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.')

    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

