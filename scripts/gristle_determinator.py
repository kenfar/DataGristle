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

#--- gristle modules -------------------
sys.path.append('../')     # allows running out of project structure
sys.path.append('../../')  # allows running out of project structure

import gristle.file_type           as file_type 
import gristle.field_determinator  as field_determinator


QUOTE_DICT = {}
QUOTE_DICT[0] = 'QUOTE_MINIMAL'
QUOTE_DICT[1] = 'QUOTE_ALL'
QUOTE_DICT[2] = 'QUOTE_NONNUMERIC'
QUOTE_DICT[3] = 'QUOTE_NONE'

#import pprint as pp
#from pprint import pprint as pp
#pp(sys.path)


#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Allows users to directly call file_determinator() from command line
    """
    (opts, dummy) = get_opts_and_args()
    my_file       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)
    my_file.analyze_file()

    if not opts.silent:
        print_file_info(my_file)

    if opts.brief:
        return 0

    # Get Analysis on ALL Fields:
    my_fields = field_determinator.FieldDeterminator(opts.filename,
                                  my_file.format_type,
                                  my_file.field_cnt,
                                  my_file.has_header,
                                  my_file.dialect,
                                  my_file.delimiter,
                                  opts.recdelimiter,
                                  opts.verbose)
    
    if opts.column_type_overrides:
        assert max(opts.column_type_overrides) < my_file.field_cnt,   \
           "ERROR: column_type_override references non-existing column_number"

    my_fields.analyze_fields(opts.column_number, opts.column_type_overrides)

    if not opts.silent:
        print print_field_info(my_fields, opts.column_number)

    return 0     


def print_file_info(my_file):
    """ Prints information about the file structure
    """
    print 
    print 'File Structure:'
    print '  format type:       %s'     % my_file.format_type
    print '  field cnt:         %d'     % my_file.field_cnt
    print '  record cnt:        %d'     % my_file.record_cnt
    print '  has header:        %s'     % my_file.has_header

    print '  delimiter:         %-6s  ' % my_file.delimiter
    print '  csv quoting:       %-6s  ' % my_file.csv_quoting
    print '  skipinitialspace:  %r'     % my_file.dialect.skipinitialspace
    print '  quoting:           %-6s  ' % QUOTE_DICT[my_file.dialect.quoting]
    print '  doublequote:       %-6r  ' % my_file.dialect.doublequote
    print '  quotechar:         %-6s  ' % my_file.dialect.quotechar
    print '  lineterminator:    %r'     % my_file.dialect.lineterminator
    print '  escapechar:        %-6r'   % my_file.dialect.escapechar
    print

def print_field_info(my_fields, column_number):
    """ Prints information about each field within the file.
    """
    print
    print 'Fields Analysis Results: '
    for sub in range(my_fields.field_cnt):
        if column_number is not None \
        and sub != column_number:
            continue

        print 
        print '      ------------------------------------------------------'
        print '      Name:           %-20s ' %  my_fields.field_names[sub]
        #print '      Name:           %-20s ' %  my_fields.field_names[sub][0]
        print '      Field Number:   %-20s ' %  sub
        if my_fields.field_trunc[sub]:
            print '      Data Truncated: analysis will be partial'

        print '      Type:           %-20s ' %  my_fields.field_types[sub]
        print '      Min:            %-20s ' %  my_fields.field_min[sub]
        print '      Max:            %-20s ' %  my_fields.field_max[sub]
        print '      Unique Values:  %-20d ' %  len(my_fields.field_freqs[sub])
        print '      Known Values:   %-20d ' %  len(my_fields.get_known_values(sub))

        if my_fields.field_types[sub] in ('integer','float'):
            print '      Mean:           %-20s ' % my_fields.field_mean[sub]
            print '      Median:         %-20s ' % my_fields.field_median[sub]
            print '      Variance:       %-20s ' % my_fields.variance[sub]
            print '      Std Dev:        %-20s ' % my_fields.stddev[sub]
        elif my_fields.field_types[sub] == 'string':
            print '      Case:           %-20s ' %   my_fields.field_case[sub]
            print '      Min Length:     %-20s ' %   my_fields.field_min_length[sub]
            print '      Max Length:     %-20s ' %   my_fields.field_max_length[sub]
            print '      Mean Length:    %-20.2f' %  my_fields.field_mean_length[sub]

        #for key in my_fields.field_freqs[0]:
        #    print 'key: %s           value: %s' % (key, my_fields.field_freqs[0][key])

        key_sub = 0
        val_sub = 1
        if my_fields.field_freqs[sub] is not None:
            sorted_list = my_fields.get_top_freq_values(sub, limit=10)
            if sorted_list[key_sub][val_sub] == 1:
                print '      Top Values not shown - all values are unique'
            else:
                print     '      Top Values: '
                for pair in sorted_list:
                    print '         %-20s x %d occurrences' % \
                          ( pair[key_sub], pair[val_sub])
    


def get_opts_and_args():
    """ gets opts & args and returns them
        run program with -h or --help for command line args
    """
    use = ("%prog determines file structure then analyzes contents of each "
           "column.\n"
           "Once complete it then prints the results for the user\n"
           "\n"
           "Usage: %prog -f [file] [misc options]"
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
           help=('Restrict analysis to a single column (field number)'
                 ' - using a zero-offset'))
    parser.add_option('-d', '--delimiter',
           help=('Specify a quoted field delimiter.'
                 'This is essential for multi-column delimiters.'))
    parser.add_option('--recdelimiter',
           help='Specify a quoted end-of-record delimiter. ')
    parser.add_option('--hasheader',
           default=False,
           action='store_true',
           help='Indicates that there is a header in the file. ')
    parser.add_option('-T', '--types',
           type='string',
           dest='column_types',
           help=('Allows manual specification of field types: integer, float, '
                 'string, timestamp. Use format: "colno:type, colno:type, '
                 ' colno:type"'))

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

    # set up column_type_overrides
    opts.column_type_overrides = {}
    if opts.column_types:
        for col_type_pair in opts.column_types.split(','):
            try:
                (col_no, col_type) = col_type_pair.split(':')
                try:
                    int(col_no)
                except ValueError:
                    parser.error('invalid column number for types option')
                if col_type not in ['integer', 'float', 'string', 'timestamp']:
                    parser.error('invalid type for types option')
            except ValueError:
                parser.error('invalid format for types option')
            opts.column_type_overrides[int(col_no)] = col_type

    return opts, args



if __name__ == '__main__':
    sys.exit(main())

