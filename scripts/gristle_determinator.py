#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - main function
      - get_opts_and_args function

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')  # allows running out of project structure

import gristle.file_type           as file_type 
import gristle.field_type          as typer
import gristle.field_determinator  as field_determinator


QUOTE_DICT = {}
QUOTE_DICT[0] = 'QUOTE_MINIMAL'
QUOTE_DICT[1] = 'QUOTE_ALL'
QUOTE_DICT[2] = 'QUOTE_NONNUMERIC'
QUOTE_DICT[3] = 'QUOTE_NONE'

#from pprint import pprint as pp
#pp(sys.path)


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Allows users to directly call file_determinator() from command line
    """
    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    MyFile.analyze_file()

    if not opts.silent:
        print_file_info(MyFile)

    if opts.brief:
        return 0

    # Get Analysis on ALL Fields:
    MyFields = field_determinator.FieldDeterminator(opts.filename,
                                  MyFile.format_type,
                                  MyFile.field_cnt,
                                  MyFile.has_header,
                                  MyFile.dialect,
                                  MyFile.delimiter,
                                  opts.recdelimiter,
                                  opts.verbose)
    MyFields.analyze_fields(opts.column_number)

    if not opts.silent:
        print print_field_info(MyFields, opts.column_number)

    return 0     


def print_file_info(MyFile):
    print 
    print 'File Structure:'
    print '  format type      = %s'     % MyFile.format_type
    print '  field_cnt        = %d'     % MyFile.field_cnt
    print '  record_cnt       = %d'     % MyFile.record_cnt
    print '  has header       = %s'     % MyFile.has_header

    print '  delimiter        = %-6r  ' % MyFile.delimiter
    print '  csv_quoting      = %-6r  ' % MyFile.csv_quoting
    print '  skipinitialspace = %r'     % MyFile.dialect.skipinitialspace
    print '  quoting          = %-6r  ' % QUOTE_DICT[MyFile.dialect.quoting]
    print '  doublequote      = %-6r  ' % MyFile.dialect.doublequote
    print '  quotechar        = %-6r  ' % MyFile.dialect.quotechar
    print '  lineterminator   = %r'     % MyFile.dialect.lineterminator
    print '  escapechar       = %-6r'   % MyFile.dialect.escapechar
    print

def print_field_info(MyFields, column_number):
    print
    print 'Fields Analysis Results: '
    for sub in range(MyFields.field_cnt):
        if column_number is not None \
        and sub != column_number:
            continue

        print 
        print '      ------------------------------------------------------'
        print '      Name:           %-20s ' %  MyFields.field_names[sub]
        print '      Field Number:   %-20s ' %  sub
        if MyFields.field_trunc[sub]:
            print '      Data Truncated: analysis will be partial'

        print '      Type:           %-20s ' %  MyFields.field_types[sub]
        print '      Min:            %-20s ' %  MyFields.field_min[sub]
        print '      Max:            %-20s ' %  MyFields.field_max[sub]
        print '      Unique Values:  %-20d    known:  %-20d' %   \
                         (len(MyFields.field_freqs[sub]),
                          len(MyFields.get_known_values(sub)))

        if MyFields.field_types[sub] in ('integer','float'):
            print '      Mean:           %-20s ' % MyFields.field_mean[sub]
            print '      Median:         %-20s ' % MyFields.field_median[sub]
            print '      Variance:       %-20s ' % MyFields.variance[sub]
            print '      Std Dev:        %-20s ' % MyFields.stddev[sub]
        elif MyFields.field_types[sub] == 'string':
            print '      Case:           %-20s ' %   MyFields.field_case[sub]
            print '      Min Length:     %-20s ' %   MyFields.field_min_length[sub]
            print '      Max Length:     %-20s ' %   MyFields.field_max_length[sub]
            print '      Mean Length:    %-20.2f' %  MyFields.field_mean_length[sub]

        #for key in MyFields.field_freqs[0]:
        #    print 'key: %s           value: %s' % (key, MyFields.field_freqs[0][key])

        key_sub = 0
        val_sub = 0
        if MyFields.field_freqs[sub] is not None:
            sorted_list = MyFields.get_top_freq_values(sub, limit=10)
            if sorted_list[key_sub][val_sub] == 1:
                print '      Top Values not shown - all values are unique'
            else:
                print     '      Top Values: '
                for pair in sorted_list:
                    print '         %-20s x %d occurances' % \
                          ( pair[key_sub], pair[val_sub])
    


def get_opts_and_args():
    """ gets opts & args and returns them
        run program with -h or --help for command line args
    """
    # get args
    use = "Usage: %prog -f [file] -q -v -b -c [column-number] --delimiter [quoted delimiter] --hasheader"
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
    parser.add_option('-s', '--silent',
                      action='store_true',
                      dest='silent',
                      default=False,
                      help='performs operation with no output')
    parser.add_option('-b', '--brief',
                      action='store_true',
                      dest='brief',
                      default=False,
                      help='skips field-level analysis')
    parser.add_option('-c', '--column',
                      type=int,
                      dest='column_number',
                      help='restrict analysis to a single column (field number) - using a zero-offset')
    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter - essential for multi-column delimiters.  Delimiter must be quoted.')
    parser.add_option('--recdelimiter',
                      help='specify an end-of-record delimiter.  The deimiter must be quoted.')
    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.  Essential for multi-column delimited files.')


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    if opts.brief and opts.column_number:
        parser.error('must not specify both brevity and column number')

    if opts.silent:
        opts.verbose = False

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

