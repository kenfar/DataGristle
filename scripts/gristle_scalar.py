#!/usr/bin/env python
""" Prints a frequency distribution of a single column from the input file.

    Example usage:
      - $ gristle_scalar.py -f ../data/state_crime.csv -c 2 -t float -a avg 
      - $ 23045.79
    
    Limitations:
      - Can only handle csv files
      - Can only process a single column
      - Does not check on max size for countdistinct or freq operations - so
        very large files could run out of memory.
      - Can only process a single file

    To do:
      - Eliminate col type arg or at least automate some of it
      - Add max dictionary checks for freq & countdistinct operations
      - Add actions: stddev & count
      - Add actions: countknown & countunknown
      - Add ability to process multiple columns simultaneously
      - Improve design of how actions run and how intermediate data is stored

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
import collections
#from pprint import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure test dir
import gristle.file_type           as file_type 

#--- global variables ------------------
temp_value = None
temp_dict  = collections.defaultdict(int)


def main():
    """ runs all processes:
            - gets opts & args
            - analyzes file to determine csv characteristics
            - runs each input record through process_value to get output
            - writes records
    """
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename,
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
                                       
    my_file.analyze_file()

    rec_cnt = 0
    csvfile = open(my_file.fqfn, "r")
    for rec in csv.reader(csvfile, my_file.dialect):
        rec_cnt      += 1
        if (opts.hasheader 
            and rec_cnt == 1): 
            continue
        else:
            converted_column = type_converter(rec[opts.column_number], 
                                              opts.column_type)
            process_value(converted_column, opts.action)
    csvfile.close()

    if (opts.hasheader
    and rec_cnt > 0):
        process_cnt = rec_cnt - 1
    else:
        process_cnt = rec_cnt

    if opts.action in ['sum', 'min', 'max']:
        print temp_value
    elif opts.action == 'avg':
        print temp_value / process_cnt
    elif opts.action == 'freq':
        for key in temp_dict:
            print '%s - %d' % (key, temp_dict[key])
    elif opts.action == 'countdistinct':
        print len(temp_dict)


    return 


def type_converter(value, column_type):
    """ Converts a single value to the type indicated.  Returns either that or
        None.
    """

    if column_type == 'integer':
        try:
            return int(value)
        except TypeError:
            return None        
    elif column_type == 'float':
        try:
            return float(value)
        except TypeError:         # catch strings
            return None         
        except ValueError:        # catch empty input
            return None
    else:
        return value



def process_value(value, action):
    """ Runs scalar action on a single row's column value.  Intermediate values
        are stored in global variables for now.
    """
    global temp_value

    if action == 'sum':
        if value:
            if temp_value is None:
                temp_value = value
            else:
                temp_value += value
    elif action == 'avg':
        temp_value += value
    elif action == 'min':
        if (temp_value is None 
            or value < temp_value):
            temp_value = value
    elif action == 'max':
        if value > temp_value:
            temp_value = value
    elif action == 'freq':
        temp_dict[value] += 1
    elif action == 'countdistinct':
        temp_dict[value] += 1
        



def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("%prog is used to perform a single scalar operation on one column "
           "within an input file. \n "
           "Potential scalar operations include Sum, AVG, Min, Max, Freq, and"
           " CountDistinct"
           "\n"
           "   %prog -v -f [file] [misc options]"
           "   example:  %prog -f ../data/state_crime.csv -c 2 -t float -a avg"
           "\n")
    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', 
           dest='filename', 
           help='input file')
    parser.add_option('-c', '--column',
           type=int,
           dest='column_number')
    parser.add_option('-t', '--column_type',
           choices=['integer', 'float', 'string'],
           help='column type:  integer, float or string')
    parser.add_option('-a', '--action',
           choices=['min', 'max', 'avg', 'sum', 'freq', 'countdistinct'],
           help=('scalar action to be performed:  min, max, avg, sum, freq, '
                 'countdistinct'))
    parser.add_option('-d', '--delimiter',
           help='specify a field delimiter.  Delimiter must be quoted.')
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

    if opts.action == 'string':
        assert(opts.action in ['min', 'max', 'freq', 'countdistinct'])

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

