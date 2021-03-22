#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""

import csv
import _csv
import fileinput
import os.path
from pprint import pprint as pp
from typing import Optional, List

import datagristle.common as comm



def get_quote_number(quote_name: str) -> int:
    """ used to help applications look up quote names typically provided by users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
    """
    return csv.__dict__[quote_name.upper()]



def get_quote_name(quote_number: int) -> str:
    """ used to help applications look up quote names based on the number
        users.
    """
    for key, value in csv.__dict__.items():
        if value == quote_number:
            return key
    else:
        raise ValueError('invalid quote_number: {}'.format(quote_number))



class Dialect(csv.Dialect):
    def __init__(self,
                 delimiter: str,
                 has_header: bool,
                 quoting: int,
                 quotechar: str = None,
                 doublequote: Optional[str] = None,
                 escapechar: Optional[str] = None,
                 lineterminator: Optional[str] = None,
                 skipinitialspace: Optional[bool] = None) -> None:

        assert quoting in [None, csv.QUOTE_NONE, csv.QUOTE_MINIMAL, csv.QUOTE_ALL, csv.QUOTE_NONNUMERIC]

        skipinitialspace = False if skipinitialspace is None else skipinitialspace
        lineterminator = lineterminator or '\n'
        quotechar = quotechar or '"'

        self.delimiter = delimiter
        self.doublequote = doublequote
        self.escapechar = escapechar
        self.lineterminator = lineterminator
        self.quotechar = quotechar
        self.quoting = quoting
        self.skipinitialspace = skipinitialspace
        self.has_header = has_header



def get_dialect(infiles: List[str],
                delimiter: Optional[str],
                quoting: Optional[str],
                quotechar: Optional[str],
                has_header: Optional[bool],
                doublequote: Optional[bool],
                escapechar: Optional[str],
				skipinitialspace: Optional[bool],
                verbosity: Optional[str]) -> Dialect:
    """ Get the csv dialect from an inspection of the file and user input
        Raises:
            - EOFError if manual inspection of the file determines that it is empty.
    """

    if infiles[0] == '-':
        final_dialect = Dialect(delimiter=delimiter,
                                quoting=get_quote_number(quoting),
                                quotechar=quotechar,
                                has_header=has_header,
                                doublequote=doublequote,
                                escapechar=escapechar,
                                skipinitialspace=skipinitialspace)
    else:
        detected_dialect = None
        try:
           for infile in infiles:
                if os.path.getsize(infile) > 0:
                    detected_dialect = autodetect_dialect(infile, read_limit=5000)
                    break
        except _csv.Error:
            detected_dialect = get_empty_dialect()
        else:
            if not detected_dialect:
                raise EOFError

        final_dialect = override_dialect(detected_dialect,
                                         delimiter=delimiter,
                                         quoting=quoting,
                                         quotechar=quotechar,
                                         has_header=has_header,
                                         doublequote=doublequote,
                                         escapechar=escapechar,
                                         skipinitialspace=skipinitialspace)

    if not is_valid_dialect(final_dialect):
       print_dialect(final_dialect)
       comm.abort('Error: invalid csv dialect',
                  'Unable to auto-detect all csv dialect attributes - please explicitly provide them',
                  verbosity)
    return final_dialect



def get_empty_dialect():
    return Dialect(delimiter=None,
                   quoting=None,
                   quotechar=None,
                   has_header=None,
                   escapechar=None,
                   doublequote=None,
                   skipinitialspace=None)



def override_dialect(dialect: Dialect,
                     delimiter: Optional[str],
                     quoting: Optional[str],
                     quotechar: Optional[str],
                     has_header: Optional[bool],
                     doublequote: Optional[bool],
                     escapechar: Optional[str],
                     skipinitialspace: Optional[bool]) -> Dialect:
    """ Consolidates individual dialect fields with a csv Dialect structure.

        Most commonly used by entry points / scripts to combine explicit csv dialect fields
        provided by a user with the dialect returned by inspection of the file.  This is
        sometimes needed if the sniffing/inspection is wrong.  But it is generally not provided
        by the user and so these values will usually be None.
    """

    dialect.delimiter = delimiter or dialect.delimiter

    if quoting is not None:
        dialect.quoting = get_quote_number(quoting)
    elif dialect.quoting is not None:
        pass
    else:
        dialect.quoting = get_quote_number('quote_none')

    dialect.quotechar  = quotechar or dialect.quotechar

    try:
        dialect.has_header = coalesce_not_none(has_header, dialect.has_header, False)
    except AttributeError:
        dialect.has_header = False

    dialect.doublequote = doublequote if doublequote is not None else dialect.doublequote
    dialect.escapechar = escapechar or dialect.escapechar
    dialect.skipinitialspace = skipinitialspace if skipinitialspace is not None else dialect.skipinitialspace
    dialect.lineterminator = '\n'

    return dialect


def coalesce_not_none(*vals):
    for val in vals:
        if val is not None:
            return val
    else:
        return None


def is_valid_dialect(dialect) -> bool:
    # note that we're not checking escapechar for None - since that's valid.
    if (dialect.delimiter is None
        or dialect.quoting is None
        or dialect.quotechar is None
        or dialect.has_header is None
        or dialect.doublequote is None):
        return False
    return True


def print_dialect(dialect) -> None:
    print(f'Dialect: ')
    print(f'    delimiter:              {dialect.delimiter}')
    print(f'    quoting:                {dialect.quoting}')
    print(f'    quoting (translated):   {get_quote_name(dialect.quoting) if dialect.quoting else None}')
    print(f'    has_header:             {dialect.has_header}')
    print(f'    doublequote:            {dialect.doublequote}')
    print(f'    escapechar:             {dialect.escapechar}')



def autodetect_dialect(fqfn: str,
                       read_limit: int = 5000) -> csv.Dialect:
    """ gets the dialect for a file
        Uses the csv.Sniffer class
        Then performs additional processing to try to improve accuracy of quoting.
    """
    # Verify we have an actual file - not an input stream:
    assert os.path.isfile(fqfn)

    with open(fqfn, 'rt') as csvfile:
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(read_limit))
            dialect.lineterminator = '\n'
        except _csv.Error:
            #This shouldn't raise error here - since it may get overridden later
            dialect = get_empty_dialect()

    # See if we can improve quoting accuracy:
    dialect.quoting = _get_dialect_quoting(dialect, fqfn)

    # Populate the has_header attribute:
    dialect.has_header = _get_has_header(fqfn, read_limit)

    return dialect



def _get_dialect_quoting(dialect: csv.Dialect,
                         fqfn: str) -> int:
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

    for rec in fileinput.input(fqfn):
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




def _get_has_header(fqfn: str,
                   read_limit: int=50000) -> bool:
    """ Figure out whether or not there's a header based on the first 50,000 bytes
    """
    sample = open(fqfn, 'r').read(read_limit)
    #todo: following line can throw an except - we should catch it
    return csv.Sniffer().has_header(sample)



