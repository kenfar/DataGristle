#!/usr/bin/env python
""" Compares two input files and prints the differences.  Unlike the diff utility
    it is file structure-aware and is both more accurate and more detailed.

    Two ways of performing the comparisons have been implemented:
       - unsorted input files:  for smaller files - all processing is performed in memory
       - sorted input files:  for larger files - minimal memory used - not
         implemented yet

    Features that should be added include:
       - sorted input files + sorting the files from within this program
       - multi-char delimiters
       - compare column exceptions (compare everything except col x)
       - print only counts - or only 1 count (ex:  print only total number of differences)
       - better structured printed of differences
       - option to print 'same' records
       - options to transform data prior to comparison: to change case, trim spaces,
         etc
 
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
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure test directory

import gristle.file_type           as file_type 


def main():
    """ runs all processes:
            - gets opts & args
            - analyzes file to determine csv characteristics
            - compares files
            - writes counts
    """
    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.file1,
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
                                       
    MyFile.analyze_file()

    if opts.sorted:
       file_diff(opts)
    else:
       (f1_cnt, f2_cnt, f1only_cnt, f2only_cnt, same_cnt, chg_cnt) = \
           dict_diff(opts, MyFile.dialect, opts.maxsize, opts.verbose, opts.casecompare)   

    if opts.verbose:
       print 
       print 'Counts: '
       print '   File1 records:        %d' % f1_cnt
       print '   File2 records:        %d' % f2_cnt
       print '   In file1 only:        %d' % f1only_cnt
       print '   In file2 only:        %d' % f2only_cnt
       print '   Same:                 %d' % same_cnt
       print '   Changed:              %d' % chg_cnt



def file_diff(opts):
    """ Assumes both input files are sorted in ascending order by the key, this 
        function performs the delta operation by walking through the two files
        in synch.  The purpose is to minimize memory usage.

        Not supported yet
    """
    pass


def dict_diff(opts, dialect, maxsize, verbose, casecompare):
    """ This delta operation is useful for small & unsorted files since it 
        uses a dictionary-based delta operation that does not require sorting - but
        is otherwise slow and memory-intensive.
   
        Inputs:
          - options - for file names, key & comparison columns
          - dialect
          - maxsize - for maximum number of rows to store in memory
          - verbose - to deterine how much to print
          - casecompare - to turn case-aware compares on & off
      
        Outputs:
          - various counts

        Limitations:
          - does not identify records that are identical
          - requires a unique key
          - requires both files to have keys & comparison columns in identical
            locations  
  
        To do:
          - should probably turn this into a class
    """

    f1kv = keyval_manager(opts.file1, dialect, opts.keycol, opts.comparecol, opts.maxsize, casecompare)
    f1kv.reader()

    f2kv = keyval_manager(opts.file2, dialect, opts.keycol, opts.comparecol, opts.maxsize, casecompare)
    f2kv.reader()

    f1only_cnt = 0
    f2only_cnt = 0
    same_cnt   = 0
    chg_cnt    = 0

    for key in f1kv.kv.keys():
        if key not in f2kv.kv:
            print 'In file1 only:           %s' % key
            f1only_cnt += 1

    for key in f2kv.kv.keys():
        if key not in f1kv.kv:
            print 'In file2 only:           %s' % key
            f2only_cnt += 1

    for key in f1kv.kv.keys():
        if key in f2kv.kv:
            if f1kv.kv[key] != f2kv.kv[key]:
                chg_cnt += 1
                print 'In both but different:   %s' % key
                if verbose:
                    print '      file1 data: %s' % f1kv.kv[key]
                    print '      file2 data: %s' % f2kv.kv[key]
            else:
                same_cnt += 1

    return f1kv.rec_cnt, f2kv.rec_cnt, f1only_cnt, f2only_cnt, same_cnt, chg_cnt



class keyval_manager(object):

    def __init__(self, filename, dialect, key_cols, comp_cols, max_size, casecompare=True):
        self.filename    = filename
        self.dialect     = dialect
        self.key_cols    = key_cols
        self.comp_cols   = comp_cols
        self.max_size    = max_size
        self.casecompare = casecompare
        self.kv          = {}
        self.rec_cnt     = 0
        self.truncated   = False

    def reader(self):

        with open(self.filename,'r') as f:
            for fields in csv.reader(f, dialect=self.dialect):
                self.rec_cnt += 1
                if self.rec_cnt == 1 and self.dialect.has_header:
                    continue
                key          = self._get_key(fields)
                value        = self._get_value(fields)
                self.kv[key] = value
                if len(self.kv) >= self.max_size:
                    print '      WARNING: kv dict is too large - will truncate'
                    self.truncated = True
                    break

    def _caserule(self, field):
        if self.casecompare:
            return field
        else:
            return field.lower()

    def _get_key(self, fields):
        """ Returns a string of concatenated keys based on the input fields of a
            single record as well as the previously-provided key list

            to do:
               - support key-ranges (ex:  5:9)
        """
        key        = ''
        concat_key = ''
        key_list = self.key_cols.split(',')
        for key_item in key_list:
            concat_key += fields[int(key_item)].strip()
        return self._caserule(concat_key)

    def _get_value(self, fields):
        """ Returns a string of concatenated values, or fields to be compared,
            based on the input fields of a single record as well as the 
            previously-provided comparison-column list
            
            to do:
               - support col-ranges (ex:  5:9)
        """
        value        = ''
        concat_value = ''
        value_list = self.comp_cols.split(',')
        for value_item in value_list:
            concat_value += fields[int(value_item)].strip()
        return self._caserule(concat_value)



def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("%prog is used to compare two files and writes the differences to stdout: \n"
          + "   %prog -v -f [file] -d [delimiter value] -c [inclusion criteria] -C [exclusion criteria]  "
          + " --delimiter [quoted delimiter] --recdelimiter [quoted record delimiter] --hasheader --help \n"
          + "   example:  %prog -1 ../data/*tiny_a* -2 ../data/*tiny_b* -k 0 -c 1,2 -v")


    parser = optparse.OptionParser(usage = use)

    parser.add_option('-v', '--verbose',
                      default=False,
                      action='store_true')

    parser.add_option('-1', '--file1', help='file1')
    parser.add_option('-2', '--file2', help='file2')

    parser.add_option('-k', '--keycol',
                      help='these are the columns that make up a unique row')
    parser.add_option('-c', '--comparecol',
                      help='these are the columns to compare')
    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter.  Delimiter must be quoted.')
    parser.add_option('-s', '--sorted',
                      default=False,
                      action='store_true',
                      help='files need to be sorted by key if they are very large - not implemented yet')
    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.')
    parser.add_option('--recdelimiter')
    parser.add_option('--maxsize',
                      default=10000,
                      help='can override max number of rows to collect')
    parser.add_option('--casecompare',
                      default=True,
                      action='store_false',
                      help='Turns case-aware compares on and off.  Default is True (on)')


    (opts, args) = parser.parse_args()

    if opts.file1 is None:
        parser.error("Error:  no filename was provided")
    elif not os.path.exists(opts.file1):
        parser.error("file1 %s could not be accessed" % opts.file1)

    if opts.sorted:
        parser.error("the sorted option has not been implemented yet")

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

