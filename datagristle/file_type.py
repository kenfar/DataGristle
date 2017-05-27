#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import os
import sys
import fileinput
import collections
import csv
import errno
from os.path import isfile
from pprint import pprint

#--- datagristle modules ------------------
import datagristle.common as comm


def get_quote_number(quote_name):
    """ used to help applications look up quote names typically provided by
        users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
        Note that if a quote_number is accidently passed to this function, it
        will simply pass it through.
    """
    if quote_name is None:
        return None
    elif comm.isnumeric(quote_name):
        return int(quote_name)
    else:
        try:
            return csv.__dict__[quote_name.upper()]
        except KeyError:
            raise ValueError('Invalid quote_name: %s' % quote_name)

def get_quote_name(quote_number):
    """ used to help applications look up quote numbers typically provided by
        users.
    """
    if not comm.isnumeric(quote_number):
        raise ValueError('Invalid quote_number: %s' % quote_number)

    for key, value in csv.__dict__.items():
        if value == int(quote_number):
            return key
    raise ValueError('Invalid quote_number: %s' % quote_number)


#------------------------------------------------------------------------------
# file determination section
#------------------------------------------------------------------------------
class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - csv_quoting
          - dialect
          - record_cnt
    """

    def __init__(self,
                 fqfn,
                 delimiter=None,
                 rec_delimiter=None,   #unused
                 has_header=None,
                 quoting='quote_none',
                 quote_char=None,
                 read_limit=-1):
        """
             Arguments - most are optional because dialect is optional
                - fqfn = fully qualified file name
                - read_limit = default is -1, which means unlimited
        """
        assert read_limit is not None
        self._delimiter           = delimiter
        self._has_header          = has_header
        self._quoting_num         = get_quote_number(quoting)
        self.fqfn                 = fqfn
        self.format_type          = None
        self.fixed_length         = None
        self.field_cnt            = None
        self.record_cnt           = None
        self.record_cnt_is_est    = None
        self.csv_quoting          = None
        self.dialect              = None
        self.read_limit           = read_limit

    def analyze_file(self):
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        if os.path.getsize(self.fqfn) == 0:
            raise IOErrorEmptyFile("Empty File")

        if self._delimiter:                                 #delimiter overridden
            self.dialect                  = csv.Dialect
            self.dialect.delimiter        = self._delimiter
            self.dialect.skipinitialspace = False
            if self._quoting_num is None:
                self._quoting_num         = csv.QUOTE_MINIMAL
            self.dialect.quoting          = self._quoting_num
            self.dialect.quotechar        = '"'             #naive default
            self.dialect.lineterminator   = '\n'
        else:
            self.dialect                  = self._get_dialect()
            self.dialect.lineterminator   = '\n'
            self._quoting_num             = self.dialect.quoting
            self._delimiter               = self.dialect.delimiter

        if self.dialect.quoting == csv.QUOTE_NONE:
            self.csv_quoting = False  # almost never see this value
        else:
            self.csv_quoting = True

        self.format_type         = self._get_format_type()
        self.dialect.has_header  = self._get_has_header(self._has_header)
        self._has_header         = self.dialect.has_header

        # unrelated to dialect, actually uses csv dialect info:
        self.field_cnt           = self._get_field_cnt()
        self.record_cnt, self.record_cnt_is_est = self._count_records()

        return self.dialect


    def _get_dialect(self):
        """ gets the dialect for a file
            Uses the csv.Sniffer class
            Then performs additional processing to try to improve accuracy of
            quoting.
        """
        csvfile = open(self.fqfn, "rt")
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(50000))
        except:
            raise IOError('could not analyse file - you may want to provide explicit csv delimiter, quoting, etc')
        csvfile.close()

        # See if we can improve quoting accuracy:
        dialect.quoting = self._get_dialect_quoting(dialect)

        return dialect



    def _get_dialect_quoting(self, dialect):
        """ Since Sniffer tends to default to QUOTE_MINIMAL we're going to try to
            get a more accurate guess.  In the event that there's an extremely
            consistent set of data that is either all quoted or not quoted at
            all we will return that appropriate value.
        """

        # total_field_cnt has a key for each number of fields found in a
        # record, and a value that indicates how often this total was found
        total_field_cnt  = collections.defaultdict(int)

        # quoted_field_cnt has a key for each number of quoted fields found
        # in a record, and a value that indicates how often this total was
        # found.
        quoted_field_cnt = collections.defaultdict(int)

        for rec in fileinput.input(self.fqfn):
            fields = rec[:-1].split(dialect.delimiter)
            total_field_cnt[len(fields)] += 1

            quoted_cnt = 0
            for field in fields:
                if len(field) >= 2:
                    if field[0] == '"' and field[-1] == '"':
                        quoted_cnt += 1
            quoted_field_cnt[quoted_cnt] += 1

            if fileinput.lineno() > 1000:
                break
        fileinput.close()

        # "Exact" scenario: simplest and most clear in which we have no confusing
        # data, every record has the same number of fields and either all are quoted
        # or none are.  This is handled specially since it's often screwed up 
        # by the Sniffer, and it's a common situation.
        if (len(total_field_cnt) == 1
        and len(quoted_field_cnt) == 1):
            if total_field_cnt[0] == quoted_field_cnt [0]:
                return csv.QUOTE_ALL
            elif quoted_field_cnt[0] == 0:
                return csv.QUOTE_NONE

        # "Almost Exact" scenario: almost the same as with the exact scenario
        # above, but in this case it allows for a few malformed records.
        # The numbers must be nearly identical - with both the most common field
        # count and most common quoted field count occuring 95% of the time.
        common_field_key, common_field_pct               = \
                   comm.get_common_key(total_field_cnt)
        common_quoted_field_key, common_quoted_field_pct = \
                   comm.get_common_key(quoted_field_cnt)

        if (common_field_pct > .95 
        and common_quoted_field_pct > .95):
            if common_field_key ==  common_quoted_field_key:
                return csv.QUOTE_ALL
            else:
                return csv.QUOTE_NONE

        # Final scenario - we can't make much of an improvement, it's probably
        # either QUOTED_MINIMAL or QUOTED_NONNUMERIC.  Sniffer probably labeled
        # it QUOTED_MINIMAL.
        return dialect.quoting




    def _get_has_header(self, has_header):
        """ if the has_header flag was already provided, then just return it
            back.
            Otherwise, figure out whether or not there's a header based on
            the first 50,000 bytes
        """
        #print 'has_header:  %s' % has_header
        if has_header is None:
            sample      = open(self.fqfn, 'r').read(50000)
            try:
                return csv.Sniffer().has_header(sample)
            except:
                raise IOError('Could not complete header analysis.  It may help to provide explicit header info')
        else:
            return has_header




    def _get_field_cnt(self):
        """ determines the number of fields in the file.

            To do:  make it less naive - it currently assumes that all #recs
            will have the same number of fields.  It should be improved to
            deal with bad data.
        """
        if not self._delimiter or len(self._delimiter) == 1:
            for rec in csv.reader(fileinput.input(self.fqfn), self.dialect):
                rec_len = len(rec)
                break
        else:
            print('file_type._get_field_cnt - DEPRECATED FUNCTIONALITY')
            # csv module can't handle multi-column delimiters:
            for rec in fileinput.input(self.fqfn):
                fields = rec[:-1].split(self._delimiter)
                rec_len = len(fields)
                break
        fileinput.close()

        return rec_len


    def _get_format_type(self):
        """ Determines format type based on whether or not all records
            are of the same length.

            Returns either 'csv' or 'fixed'
        """
        # our solution isn't accurate enough to show yet, so for now just 
        # set to 'csv':
        return 'csv'

        #todo:  make this smarter:
        #       - Since we're not using a csv dialect we could have control 
        #         characters breaking a row into multiple lines.
        #       - Also, a small csv file might really have all rows get the same
        #         length.
        #       - Also, the user may be passed in explicit csv dialect info.
        rec_length = collections.defaultdict(int)
        for rec in fileinput.input(self.fqfn):
            rec_length[len(rec)] += 1
            if fileinput.lineno > 1000:     # don't want to read millions of recs
                break
        fileinput.close()

        if len(rec_length) == 1:
            return 'fixed'
        else:
            return 'csv'


    def _count_records(self):
        """ Returns the number of records in the file
            Outputs:
               - rec count
               - estimated - True or False, indicates if the rec count is an
                 estimation based on the first self.read_limit rows.
        """
        rec_cnt           = 0
        estimated_rec_cnt = 0
        byte_cnt          = 0
        if self.read_limit > -1:
            estimated         = True
        else:
            estimated         = False

        if estimated:
            # fastest method, should be helpful if the read_limit is very high
            # but can miscount rows if newlines are in a field
            estimated = True
            infile  = open(self.fqfn, 'rt')
            for rec in infile:
                byte_cnt += len(rec)
                rec_cnt  += 1
                if rec_cnt  >= self.read_limit:
                    break
            infile.close()
            try:
                bytes_per_rec = byte_cnt / rec_cnt
                estimated_rec_cnt = int(os.path.getsize(self.fqfn) / bytes_per_rec) 
            except  ZeroDivisionError:
                pass

        else:
            # much slower method, but most accurate
            with open(self.fqfn, 'rt') as infile:
                reader = csv.reader(infile, self.dialect)
                for row in reader:
                    rec_cnt += 1

        return estimated_rec_cnt or rec_cnt, estimated




def get_dialect(files, delimiter, quotename, quotechar, recdelimiter, hasheader):
    """ Gets a csv dialect for a csv file or set of attributes.

    If files are provided and are not '-' -then use files and run file_type.FileTyper
    to get csv - while passing rest of args to FileTyper.  Otherwise, manually construct
    csv dialect from non-files arguments.

    Args:
        files: a list of files to analyze.  Analyze the minimum number of recs
               from the first file to determine delimiter.
        delimiter: a single character
        quotename: one of QUOTE_MINIMAL, QUOTE_NONE, QUOTE_ALL, QUOTE_NONNUMERIC
        quotechar: a single character
        recdelimiter: a single character
        hasheader: a boolean
    Returns:
        csv dialect object
    Raises:
        sys.exit - if all files are empty
    """
    assert isinstance(files, list)
    dialect = None

    if files[0] == '-':
        # dialect parameters needed for stdin - since the normal code can't
        # analyze this data.
        dialect                = csv.Dialect
        dialect.delimiter      = delimiter
        dialect.quoting        = get_quote_number(quotename)
        dialect.quotechar      = quotechar
        dialect.lineterminator = '\n'                 # naive assumption
        dialect.hasheader      = hasheader
    else:
        for fn in files:
            if not isfile(fn):
                raise ValueError('file does not exist: %s' % fn)
            my_file   = FileTyper(fn ,
                                  delimiter          ,
                                  recdelimiter       ,
                                  hasheader          ,
                                  quoting=quotename  ,
                                  quote_char=quotechar,
                                  read_limit=5000    )
            try:
                my_file.analyze_file()
                dialect = my_file.dialect
                break
            except IOErrorEmptyFile:
                continue
            else:
                # todo: is this a typo?
                sys.exit(errno.ENODATA)
        # Don't exit with ENODATA unless all files are empty:
        if dialect is None:
            sys.exit(errno.ENODATA)

    # validate quoting & assign defaults:
    if dialect.quoting is None:
        dialect.quoting = file_type.get_quote_number('quote_minimal')
    assert dialect.quoting is not None and comm.isnumeric(dialect.quoting)

    # validate delimiter & assign defaults:
    if dialect.delimiter is None:
        raise ValueError("Invalid Delimiter: %s" % dialect.delimiter)

    return dialect



class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass



