#!/usr/bin/env python2.7
""" determinator:  used to identify characteristics of a file
    contains:
      - FileTyper class
      - main function
      - get_opts_and_args function
    todo:
      - explore details around quoting flags - they seem very inaccurate
      -

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import fileinput
import collections
import optparse
import csv

#--- gristle modules -------------------
import field_determinator as fielder


QUOTE_DICT = {}
QUOTE_DICT[0] = 'QUOTE_MINIMAL'
QUOTE_DICT[1] = 'QUOTE_ALL'
QUOTE_DICT[2] = 'QUOTE_NONNUMERIC'
QUOTE_DICT[3] = 'QUOTE_NONE'



#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ Allows users to directly call file_determinator() from command line
    """
    (opts, args) = get_opts_and_args()
    MyFile       = FileTyper(opts.filename)
    MyFile.analyze_file()

    if opts.verbose:
        print_file_info(MyFile)


    if opts.brief:
       return 0

    # Get Analysis on ALL Fields:
    MyFields = fielder.FieldTyper(opts.filename,
                                  MyFile.format_type,
                                  MyFile.field_cnt,
                                  MyFile.has_header,
                                  MyFile.dialect)
    MyFields.analyze_fields(opts.column_number)

    if opts.verbose:
        print print_field_info(MyFile, MyFields)

    return 0     


def print_file_info(MyFile):
        print 
        print 'File Structure:'
        print '  format type      = %s'     % MyFile.format_type
        print '  field_cnt        = %d'     % MyFile.field_cnt
        print '  record number    = %d'     % MyFile.record_number
        print '  has header       = %s'     % MyFile.has_header

        print '  delimiter        = %-6r  ' % MyFile.dialect.delimiter
        print '  csv_quoting      = %-6r  ' % MyFile.csv_quoting
        print '  skipinitialspace = %r'     % MyFile.dialect.skipinitialspace
        print '  quoting          = %-6r  ' % QUOTE_DICT[MyFile.dialect.quoting]
        print '  doublequote      = %-6r  ' % MyFile.dialect.doublequote
        print '  quotechar        = %-6r  ' % MyFile.dialect.quotechar
        print '  lineterminator   = %r'     % MyFile.dialect.lineterminator
        print '  escapechar       = %-6r'   % MyFile.dialect.escapechar
        print

def print_field_info(MyFile, MyFields):
        print 'Fields: '
        for sub in range(MyFields.field_number):
            print 
            print '   Name:  %-20s   ' %  MyFields.field_names[sub]
            if MyFile.has_header:
               print '      Number:      %-20s ' %   sub
            print '      Type:           %-20s ' %   MyFields.field_types[sub]
            if MyFields.field_types[sub] in ('integer','float'):
                print '      Mean:           %-20s ' % MyFields.field_mean[sub]
                print '      Median:         %-20s ' % MyFields.field_median[sub]
            print '      Max:            %-20s ' %   MyFields.field_max[sub]
            print '      Min:            %-20s ' %   MyFields.field_min[sub]
            if MyFields.field_types[sub] == 'string':
               print '      Case:           %-20s ' %   MyFields.field_case[sub]

            print '      Unique Values:  %-20d    known:  %-20d' %   \
                         (len(MyFields.field_freqs[sub]),
                          len(MyFields.get_known_values(sub)))
            if MyFields.field_freqs[sub] is not None:
                sorted_list = MyFields.get_top_freq_values(sub, 4)
                print     '      Top Values: '
                for pair in sorted_list:
                    if not fielder.is_unknown_value(pair[0]): 
                       #print '         %-20.20s - %d ' % ( pair[0], pair[1])
                       print '         %-20s - %d ' % ( pair[0], pair[1])
    


def get_opts_and_args():
    """ gets opts & args and returns them
        run program with -h or --help for command line args
    """
    # get args
    use = "Usage: %prog -f [file] -q -v -b -c [column-number]"
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
    parser.add_option('-b', '--brief',
                      action='store_true',
                      dest='brief',
                      default=False,
                      help='skips field-level analysis')
    parser.add_option('-c', '--column',
                      type=int,
                      dest='field_number',
                      help='restrict analysis to a single column (field number) - using a zero-offset')


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)

    if opts.brief and opts.column_number:
        parser.error('must not specify both brevity and column number')

    return opts, args




#------------------------------------------------------------------------------
# file determination section
#------------------------------------------------------------------------------
class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - csv_quoting
          - dialect
          - record_number
          - has_header
    """

    def __init__(self, fqfn):
        """  fqfn = fully qualified file name
        """
        self.fqfn                 = fqfn
        self.has_header           = None
        self.format_type          = None
        self.fixed_length         = None
        self.field_cnt            = None
        self.record_number        = None
        self.csv_quoting          = None
        self.dialect              = None # python csv module variable

    def analyze_file(self):
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        self.format_type   = self._get_format_type()
        self.dialect       = self._get_dialect()
        self.has_header    = self._has_header()
        self.field_cnt     = self._get_field_cnt()
        self.record_number = self._count_records()
        if QUOTE_DICT[self.dialect.quoting] == 'QUOTE_NONE':
            self.csv_quoting = False
        else:
            self.csv_quoting = True

    def _get_dialect(self):
        """ gets the dialect for a file
        """
        csvfile = open(self.fqfn, "rb")
        try:
           dialect = csv.Sniffer().sniff(csvfile.read(50000))
        except:
           print 'ERROR: Could not analyze file!'
           raise
           
        csvfile.close()
        return dialect

    def _has_header(self):
        """ figure out whether or not there's a header based on the
            first 50,000 bytes
        """
        sample      = open(self.fqfn, 'r').read(50000)
        return csv.Sniffer().has_header(sample)
        
    def _get_field_cnt(self):
        """ determines the number of fields in the file.
 
            To do:  make it less naive - it currently assumes that all #recs
            will have the same number of fields.  It should be improved to 
            deal with bad data.
        """
        for row in csv.reader(open(self.fqfn,'r'), self.dialect):
            return len(row)
 
    def _get_format_type(self):
        """ Determines format type based on whether or not all records
            are of the same length.
        """
        rec_length = collections.defaultdict(int)
        rec_cnt = 0
        for rec in fileinput.input(self.fqfn):
            rec_length[len(rec)] += 1
            rec_cnt += 1
            if rec_cnt > 1000:     # don't want to read millions of recs
                break
        fileinput.close()
       
        if len(rec_length) == 1:
            return 'fixed'
        else:
            return 'csv'

    def _count_records(self):
        """ Returns the number of records in the file
        """
        rec_cnt = 0
        for rec in fileinput.input(self.fqfn):
            rec_cnt += 1
        return rec_cnt


if __name__ == '__main__':
    sys.exit(main())

