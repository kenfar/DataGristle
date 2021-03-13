#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""

import csv
import _csv
import os.path
from typing import Optional, List

import datagristle.file_type as file_type
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
                escapechar: Optional[str]) -> Dialect:
    """ Get the csv dialect from an inspection of the file and user input
        Raises:
            - EOFError if manual inspection of the file determines that it is empty.
    """

    if infiles[0] == '-':
        final_dialect = Dialect(delimiter=delimiter,
                                quoting=file_type.get_quote_number(quoting),
                                quotechar=quotechar,
                                has_header=has_header,
                                doublequote=doublequote,
                                escapechar=escapechar)
    else:
        detected_dialect = None
        try:
           for infile in infiles:
                if os.path.getsize(infile) > 0:
                    my_file = file_type.FileTyper(infile)
                    detected_dialect = my_file.analyze_file()
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
                                         escapechar=escapechar)

    if not is_valid_dialect(final_dialect):
       raise ValueError('Error: invalid csv dialect')
    return final_dialect



def get_empty_dialect():
    return Dialect(delimiter=None,
                   quoting=None,
                   quotechar=None,
                   has_header=None,
                   escapechar=None,
                   doublequote=None)



def override_dialect(dialect: Dialect,
                     delimiter: Optional[str],
                     quoting: Optional[str],
                     quotechar: Optional[str],
                     has_header: Optional[bool],
                     doublequote: Optional[bool],
                     escapechar: Optional[str]) -> Dialect:
    """ Consolidates individual dialect fields with a csv Dialect structure.

        Most commonly used by entry points / scripts to combine explicit csv dialect fields
        provided by a user with the dialect returned by inspection of the file.  This is
        sometimes needed if the sniffing/inspection is wrong.  But it is generally not provided
        by the user and so these values will usually be None.
    """

    dialect.delimiter = delimiter or dialect.delimiter

    if quoting:
        dialect.quoting = file_type.get_quote_number(quoting) if quoting else dialect.quoting
    elif dialect.quoting:
        pass
    else:
        dialect.quoting = file_type.get_quote_number('quote_none')

    dialect.quotechar  = quotechar or dialect.quotechar

    try:
        dialect.has_header = coalesce_not_none(has_header, dialect.has_header, False)
    except AttributeError:
        dialect.has_header = False

    dialect.doublequote = doublequote if doublequote is not None else dialect.doublequote
    dialect.escapechar = escapechar or dialect.escapechar
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






