#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""

import csv
import fileinput
import os.path
from pprint import pprint as pp
from typing import Optional, List, Dict, Any, Union, Type
import _csv

import datagristle.common as comm



def get_quote_number(quote_name: Optional[str]) -> Optional[int]:
    """ used to help applications look up quote names typically provided by users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
    """
    assert type(quote_name) in (str, type(None))

    if quote_name is None:
        return None
    else:
        return csv.__dict__[quote_name.upper()]



def get_quote_name(quote_number: int) -> Optional[str]:
    """ used to help applications look up quote names based on the number
        users.
    """
    assert type(quote_number) in (int, type(None))

    if quote_number is None:
        return None

    for key, value in csv.__dict__.items():
        if value == quote_number:
            return key
    else:
        raise ValueError('invalid quote_number: {}'.format(quote_number))



class Header:
    """ Manages csv header information to support the use of field names rather
        than field numbers in configs.
    """

    def __init__(self):
        self.raw_field_names = []
        self.raw_fields_by_position = {}
        self.raw_fields_by_name = {}

        self.field_names = []
        self.fields_by_position = {}
        self.fields_by_name = {}


    def load_from_file(self,
                       file_name: str,
                       dialect):

        if file_name == '-':
            comm.abort(f'Invalid file_name for Header: {file_name}')

        reader = csv.reader(open(file_name, newline=''), dialect=dialect)
        for field_names in reader:
            break
        else:
            raise EOFError

        def make_field_name_unique(starting_field_name, field_names):
            temp_field_name = starting_field_name
            for count in range(999):
                if temp_field_name in self.field_names:
                    temp_field_name = starting_field_name + f'__{count}'
                else:
                    break
            else:
                comm.abort('Error: cannot create unique header field name - 999 attempts failed')
            return temp_field_name


        for field_sub, raw_field_name in enumerate(field_names):
            if dialect.has_header:
                field_name = self.format_raw_header_field_name(raw_field_name)
            else:
                raw_field_name = field_name = f'field_{field_sub}'

            field_name = make_field_name_unique(field_name, field_names)

            self.field_names.append(field_name)
            self.fields_by_position[field_sub] = field_name
            self.fields_by_name[field_name] = field_sub

            self.raw_field_names.append(raw_field_name)
            self.raw_fields_by_position[field_sub] = raw_field_name
            self.raw_fields_by_name[raw_field_name] = field_sub

        #if len(self.field_names) != len(set(self.field_names)):
        #    comm.abort(f'Error: header has duplicate field names',
        #               f'Derrived header names: {self.field_names}')


    def format_raw_header_field_name(self, field_name):
        return field_name.strip().replace(' ', '_').lower()


    def load_from_files(self,
                        file_names: List[str],
                        dialect):
        for file_name in file_names:
            try:
                self.load_from_file(file_name, dialect)
                return
            except EOFError:
                pass
        raise EOFError


    def get_field_position(self,
                           field_name):
        return self.fields_by_name[field_name]


    def get_field_name(self,
                       field_position):
        return self.fields_by_position[field_position]


    def get_field_position_from_any(self,
                                    lookup: Union[str, int]) -> int:
        """ Returns a field position given either a field name or position
        """
        if comm.isnumeric(lookup):
             return int(lookup)
        else:
             return self.get_field_position(lookup)


    def get_field_positions_from_any(self,
                                    lookups: List[Union[str, int]]) -> List[int]:
        """ Returns a list of field positions given a list of positions or names
        """
        return [self.get_field_position_from_any(x) for x in lookups]


    def get_raw_field_name(self,
                           field_position):
        return self.raw_fields_by_position[field_position]


    def get_raw_field_position(self,
                               raw_field_name):
        return self.raw_fields_by_name[raw_field_name]






class Dialect(csv.Dialect):
    """ A simple Dialect class

    This dialect class includes has_header and minimal defaulting that make it work
    better for this application - where we want to pass around csv info, not define
    reusable dialects.
    """
    def __init__(self,
                 delimiter: Optional[str],
                 has_header: Optional[bool],
                 quoting: Optional[int],
                 quotechar: Optional[str] = None,
                 doublequote: Optional[bool] = None,
                 escapechar: Optional[str] = None,
                 lineterminator: Optional[str] = None,
                 skipinitialspace: Optional[bool] = None) -> None:

        assert quoting in [None, csv.QUOTE_NONE, csv.QUOTE_MINIMAL,
                           csv.QUOTE_ALL, csv.QUOTE_NONNUMERIC]

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

def convert_dialect(std_dialect: Type[_csv.Dialect]) -> Dialect:
    return Dialect(delimiter=std_dialect.delimiter,
                   has_header=None,
                   quoting=std_dialect.quoting,
                   quotechar=std_dialect.quotechar,
                   doublequote=std_dialect.doublequote,
                   escapechar=std_dialect.escapechar,
                   lineterminator=std_dialect.lineterminator,
                   skipinitialspace=std_dialect.skipinitialspace)


def get_dialect(infiles: List[str],
                delimiter: Optional[str] = None,
                quoting: Optional[str] = None,
                quotechar: Optional[str] = None,
                has_header: Optional[bool] = None,
                doublequote: Optional[bool] = None,
                escapechar: Optional[str] = None,
                skipinitialspace: Optional[bool] = None,
                verbosity: Optional[str] = None) -> Dialect:
    """ Get the csv dialect from an inspection of the file and user input
        Raises:
            - EOFError if manual inspection of the file determines that it is empty.

        Behavior is slightly different for piped-in data vs files:
            - piped-in data must be provided with dialect info
            - files could get auto-detected dialect
            - and files could trigger a EOFError if empty

        Note that the dialect provided may be invalid - it may have some required
        entries with a value of None.  This can be separately validated using the
        is_valid_dialect() function.
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
        except _csv.Error as e:
            # ex: _csv.Error: Could not determine delimiter
            detected_dialect = get_empty_dialect()
        else:
            if not detected_dialect:
                raise EOFError

        if verbosity == 'debug':
            print_dialect(detected_dialect, 'csvhelper.get_dialect.auto-detected')

        final_dialect = override_dialect(detected_dialect,
                                         delimiter=delimiter,
                                         quoting=quoting,
                                         quotechar=quotechar,
                                         has_header=has_header,
                                         doublequote=doublequote,
                                         escapechar=escapechar,
                                         skipinitialspace=skipinitialspace)

    return final_dialect



#def get_empty_dialect() -> datagristle.csvhelper.Dialect:
def get_empty_dialect() -> Dialect:
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
    """ Overrides the dialect with any non-None values from other args
    """
    assert isinstance(quoting, (str, type(None)))

    if delimiter is not None:
        dialect.delimiter = delimiter
    if has_header is not None:
        dialect.has_header = has_header
    if skipinitialspace is not None:
        dialect.skipinitialspace = skipinitialspace

    # Cannot have a quotechar if there's no quoting
    if quoting is not None:
        dialect.quoting = get_quote_number(quoting)
    if quotechar is not None:
        dialect.quotechar = quotechar
    if dialect.quoting is None:
        dialect.quotechar = None

    # We cannot have both doublequoting & escapechar at the same time:
    if doublequote is True:
        dialect.doublequote = True
        dialect.escapechar = None
    elif doublequote is False:
        dialect.doublequote = False

    if escapechar:
        dialect.escapechar = escapechar
        dialect.doublequote = False
    elif escapechar:
        dialect.escapechar = None

    if dialect.escapechar and dialect.doublequote:
        dialect.doublequote = True
        dialect.escapechar = None

    dialect.lineterminator = '\n'

    return dialect



def default_dialect(dialect: Dialect,
                    delimiter: Optional[str],
                    quoting: Optional[str],
                    quotechar: Optional[str],
                    has_header: Optional[bool],
                    doublequote: Optional[bool],
                    escapechar: Optional[str],
                    skipinitialspace: Optional[bool]) -> Dialect:
    """ defaults the dialect with any non-None values from other args
    """
    assert isinstance(quoting, (str, type(None)))

    if dialect.delimiter is None:
        dialect.delimiter = delimiter
    if dialect.quoting is None:
        dialect.quoting = get_quote_number(quoting)
    if dialect.quotechar is None:
        dialect.quotechar = quotechar
    if dialect.has_header is None:
        dialect.has_header = has_header
    if dialect.skipinitialspace is None:
        dialect.skipinitialspace = skipinitialspace

    # Make sure we only have either doublequoting or escapechar turned on
    if dialect.doublequote is None:
        dialect.doublequote = doublequote
    if dialect.escapechar is None:
        dialect.escapechar = escapechar
    if dialect.doublequote and dialect.escapechar:
        comm.abort('Error: cannot have both doublequoting and escapechar')

    dialect.lineterminator = '\n'

    return dialect



def is_valid_dialect(dialect) -> bool:
    # note that we're not checking escapechar for None - since that's valid.
    if (dialect.delimiter is None
            or dialect.quoting is None
            or dialect.quotechar is None
            or dialect.has_header is None
            or dialect.doublequote is None):
        return False
    if dialect.quoting not in (None, csv.QUOTE_NONE, csv.QUOTE_ALL,
                               csv.QUOTE_NONNUMERIC, csv.QUOTE_MINIMAL):
        return False
    return True


def print_dialect(dialect, name) -> None:
    print(f'{name} Dialect: ')
    print(f'    delimiter:              {dialect.delimiter}')
    print(f'    quoting:                {dialect.quoting}')
    print(f'    quoting (translated):   {get_quote_name(dialect.quoting)}')
    print(f'    has_header:             {dialect.has_header}')
    print(f'    doublequote:            {dialect.doublequote}')
    print(f'    escapechar:             {dialect.escapechar}')



def autodetect_dialect(fqfn: str,
                       read_limit: int = 5000) -> Dialect:
    """ gets the dialect for a file
        Uses the csv.Sniffer class
        Then performs additional processing to try to improve accuracy of quoting.
    """
    # Verify we have an actual file - not an input stream:
    assert os.path.isfile(fqfn)

    with open(fqfn, newline='') as csvfile:
        try:
            dialect = convert_dialect(csv.Sniffer().sniff(csvfile.read(read_limit)))
            dialect.lineterminator = '\n'
            dialect.has_header = None
        except _csv.Error:
            #This shouldn't raise error here - since it may get overridden later
            dialect = get_empty_dialect()


    # See if we can improve quoting accuracy:
    dialect.quoting = _get_dialect_quoting(dialect, fqfn)

    # Populate the escapechar attribute
    dialect.escapechar = _get_dialect_escapechar(dialect)

    # Populate the has_header attribute:
    dialect.has_header = _get_has_header(fqfn, read_limit)

    return dialect



def _get_dialect_quoting(dialect: _csv.Dialect,
                         fqfn: str) -> int:
    """ Since Sniffer tends to default to QUOTE_MINIMAL we're going to try to
        get a more accurate guess.  In the event that there's an extremely
        consistent set of data that is either all quoted or not quoted at
        all we will return that appropriate value.
    """

    # total_field_cnt has a key for each number of fields found in a
    # record, and a value that indicates how often this total was found
    #total_field_cnt  = collections.defaultdict(int)
    total_field_cnt: Dict[Any, Union[int, float]] = {}

    # quoted_field_cnt has a key for each number of quoted fields found
    # in a record, and a value that indicates how often this total was
    # found.
    #quoted_field_cnt = collections.defaultdict(int)
    quoted_field_cnt: Dict[Any, Union[int, float]] = {}

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


def _get_dialect_escapechar(dialect: _csv.Dialect):
    """ Populate the escapechar on a dialog if it is missing
    """
    if dialect.doublequote is True:
        return None
    elif 'escapechar' not in dialect.__dict__:
        return None
    else:
        return dialect.escapechar


def _get_has_header(fqfn: str,
                    read_limit: int = 50000) -> bool:
    """ Figure out whether or not there's a header based on the first 50,000 bytes
        Raises:
            - csv.Snipper() can throw exceptions if it can't interpret file
    """
    sample = open(fqfn, 'r').read(read_limit)
    return csv.Sniffer().has_header(sample)

