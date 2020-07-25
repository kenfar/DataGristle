#!/usr/bin/env python
""" Used to identify characteristics of a file
    contains:
      - FileTyper class
    todo:
      - explore details around quoting flags - they seem very inaccurate

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2020 Ken Farmer
"""
import os
import os.path
import sys
import fileinput
import collections
import csv
import errno
from os.path import isfile
from pprint import pprint
from typing import Union, Dict, List, Tuple, Any, Optional
from pprint import pprint as pp

import datagristle.common as comm
import datagristle.csvhelper as csvhelper


def get_quote_number(quote_name: str) -> int:
    """ used to help applications look up quote names typically provided by
    users.
    Inputs:
       - quote_name
    Outputs:
       - quote_number
    """
    if comm.isnumeric(quote_name):
        raise ValueError('Invalid quote_name: %s' % quote_name)
    if quote_name is None:
        raise ValueError('Invalid quote_name: %s' % quote_name)

    try:
        return int(csv.__dict__[quote_name.upper()])
    except KeyError:
        raise ValueError('Invalid quote_name: %s' % quote_name)


def get_quote_name(quote_number: Union[int, str]) -> str:
    """ used to help applications look up quote numbers typically provided by
        users.
    """
    if not comm.isnumeric(quote_number):
        raise ValueError('Invalid quote_number: %s' % quote_number)

    for key, value in csv.__dict__.items():
        if value == int(quote_number):
            return key
    else:
        raise ValueError('Invalid quote_number: %s' % quote_number)



#------------------------------------------------------------------------------
# file determination section
#------------------------------------------------------------------------------
class FileTyper(object):
    """ Determines type of file - mostly using csv.Sniffer()
        Populates public variables:
          - format_type
          - dialect
          - record_cnt
    """

    def __init__(self,
                 fqfn: str,
                 delimiter: Optional[str]=None,
                 rec_delimiter: Optional[str]=None,   #unused
                 has_header: Optional[bool]=None,
                 quoting: str='quote_none',
                 quote_char: Optional[str]=None,
                 read_limit: int=-1) -> None:
        """
             Arguments - most are optional because dialect is optional
                - fqfn = fully qualified file name
                - read_limit = default is -1, which means unlimited
        """
        assert read_limit is not None
        self._delimiter = delimiter
        self._has_header = has_header
        self._quoting_num = None if quoting is None else get_quote_number(quoting)
        self.quote_char = quote_char
        self.fqfn = fqfn
        self.format_type: Optional[str] = None
        self.field_cnt: Optional[int] = None
        self.record_cnt: Optional[int] = None
        self.record_cnt_is_est: Optional[bool] = None
        self.dialect: Optional[csvhelper.Dialect] = None
        self.read_limit: int = read_limit

    def analyze_file(self) -> csv.Dialect:
        """ analyzes a file to determine the structure of the file in terms
            of whether or it it is delimited, what the delimiter is, etc.
        """
        if os.path.getsize(self.fqfn) == 0:
            raise IOErrorEmptyFile("Empty File")

        if self._delimiter:
            if self._quoting_num is None:
                self._quoting_num = csv.QUOTE_MINIMAL
            self.dialect = csvhelper.Dialect(self._delimiter,
                                             self._get_has_header(),
                                             self._quoting_num,
                                             self.quote_char,
                                             None,
                                             None,
                                             '\n',
                                             False)
        else:
            self.dialect = self._get_dialect()
            self.dialect.lineterminator = '\n'
            self._quoting_num = self.dialect.quoting
            self._delimiter = self.dialect.delimiter

        self.format_type = self._get_format_type()
        self.dialect.has_header = self._get_has_header(self._has_header)
        self._has_header = self.dialect.has_header

        # unrelated to dialect, actually uses csv dialect info:
        self.field_cnt = self._get_field_cnt()
        self.record_cnt, self.record_cnt_is_est = self._count_records()

        return self.dialect


    def _get_dialect(self) -> csv.Dialect:
        """ gets the dialect for a file
            Uses the csv.Sniffer class
            Then performs additional processing to try to improve accuracy of
            quoting.
        """
        # Verify we have an actual file - have had problems with files & lists of files due to upstream flexibility.
        assert os.path.isfile(self.fqfn)

        with open(self.fqfn, 'rt') as csvfile:
            try:
                dialect = csv.Sniffer().sniff(csvfile.read(50000))
            except:
                raise IOError('could not analyse file - you may want to provide explicit csv delimiter, quoting, etc')

        # See if we can improve quoting accuracy:
        dialect.quoting = self._get_dialect_quoting(dialect)

        return dialect



    def _get_dialect_quoting(self, dialect: csv.Dialect) -> int:
        """ Since Sniffer tends to default to QUOTE_MINIMAL we're going to try to
            get a more accurate guess.  In the event that there's an extremely
            consistent set of data that is either all quoted or not quoted at
            all we will return that appropriate value.
        """

        # total_field_cnt has a key for each number of fields found in a
        # record, and a value that indicates how often this total was found
        #total_field_cnt  = collections.defaultdict(int)
        total_field_cnt: Dict[int, int] = {}

        # quoted_field_cnt has a key for each number of quoted fields found
        # in a record, and a value that indicates how often this total was
        # found.
        #quoted_field_cnt = collections.defaultdict(int)
        quoted_field_cnt: Dict[int, int] = {}

        for rec in fileinput.input(self.fqfn):
            fields = rec[:-1].split(dialect.delimiter)
            try:
                total_field_cnt[len(fields)] += 1
            except KeyError:
                total_field_cnt[len(fields)] = 1

            quoted_cnt = 0
            for field in fields:
                if len(field) >= 2:
                    if field[0] == '"' and field[-1] == '"':
                        quoted_cnt += 1
            try:
                quoted_field_cnt[quoted_cnt] += 1
            except KeyError:
                quoted_field_cnt[quoted_cnt] = 1

            if fileinput.lineno() > 1000:
                break
        fileinput.close()

        # "Exact" scenario: simplest and most clear in which we have no confusing
        # data, every record has the same number of fields and either all are quoted
        # or none are.  This is handled specially since it's often screwed up 
        # by the Sniffer, and it's a common situation.
        if len(total_field_cnt) == 1 and len(quoted_field_cnt) == 1:
            if list(total_field_cnt.keys())[0] == list(quoted_field_cnt.keys())[0]:
                return csv.QUOTE_ALL
            elif list(quoted_field_cnt.values())[0] == 0:
                return csv.QUOTE_NONE

        # "Almost Exact" scenario: almost the same as with the exact scenario
        # above, but in this case it allows for a few malformed records.
        # The numbers must be nearly identical - with both the most common field
        # count and most common quoted field count occuring 95% of the time.
        common_field_cnt, common_field_pct = comm.get_common_key(total_field_cnt)
        common_quoted_field_cnt, common_quoted_field_pct = comm.get_common_key(quoted_field_cnt)

        if common_field_pct > .95 and common_quoted_field_pct > .95:
            if common_field_cnt == common_quoted_field_cnt:
                return csv.QUOTE_ALL
            elif common_quoted_field_cnt == 0:
                return csv.QUOTE_NONE

        # Final scenario - we can't make much of an improvement, it's probably
        # either QUOTED_MINIMAL or QUOTED_NONNUMERIC.  Sniffer probably labeled
        # it QUOTED_MINIMAL.
        return dialect.quoting




    def _get_has_header(self, has_header: bool=None) -> bool:
        """ if the has_header flag was already provided, then just return it
            back.
            Otherwise, figure out whether or not there's a header based on
            the first 50,000 bytes
        """
        if has_header is None:
            sample = open(self.fqfn, 'r').read(50000)
            try:
                has_header = csv.Sniffer().has_header(sample)
            except:
                raise IOError('Could not complete header analysis.  It may help to provide explicit header info')
        return has_header




    def _get_field_cnt(self) -> int:
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



    def _get_format_type(self) -> str:
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


    def _count_records(self) -> Tuple[int, bool]:
        """ Returns the number of records in the file
            Outputs:
               - rec count
               - estimated - True or False, indicates if the rec count is an
                 estimation based on the first self.read_limit rows.
        """
        rec_cnt = 0
        estimated_rec_cnt = 0
        byte_cnt = 0
        estimated = True if self.read_limit > -1 else False

        if estimated:
            # fastest method, should be helpful if the read_limit is very high
            # but can miscount rows if newlines are in a field
            estimated = True
            infile = open(self.fqfn, 'rt')
            for rec in infile:
                byte_cnt += len(rec)
                rec_cnt += 1
                if rec_cnt >= self.read_limit:
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
                for _ in reader:
                    rec_cnt += 1

        return estimated_rec_cnt or rec_cnt, estimated




def get_dialect(files: List[str],
                delimiter: str,
                quotename: str,
                quotechar: str,
                recdelimiter: str,
                has_header: bool) -> csv.Dialect:
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
        has_header: a boolean
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
        dialect = csvhelper.Dialect
        dialect.delimiter = delimiter
        dialect.quoting = get_quote_number(quotename)
        dialect.quotechar = quotechar
        dialect.lineterminator = '\n'  # naive assumption
        dialect.has_header = has_header
    else:
        for fn in files:
            if not isfile(fn):
                raise ValueError('file does not exist: %s' % fn)
            my_file = FileTyper(fn,
                                delimiter,
                                recdelimiter,
                                has_header,
                                quoting=quotename,
                                quote_char=quotechar,
                                read_limit=5000)
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
        dialect.quoting = get_quote_number('quote_minimal')
    assert dialect.quoting is not None and comm.isnumeric(dialect.quoting)

    # validate delimiter & assign defaults:
    if dialect.delimiter is None:
        raise ValueError("Invalid Delimiter: %s" % dialect.delimiter)

    return dialect



class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass




