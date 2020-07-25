#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2020 Ken Farmer
"""

import csv
from typing import Optional, List

import datagristle.file_type as file_type



def get_quote_number(quote_name: str) -> int:
    """ used to help applications look up quote names typically provided by users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
        Note that if a quote_number is accidently passed to this function, it
        will simply pass it through.
    """
    return csv.__dict__[quote_name.upper()]



def get_quote_name(quote_number: int) -> str:
    """ used to help applications look up quote numbers typically provided by
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

        assert quoting in [csv.QUOTE_NONE, csv.QUOTE_MINIMAL, csv.QUOTE_ALL, csv.QUOTE_NONNUMERIC]

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
                has_header: Optional[bool]) -> Dialect:
    """ Get the csv dialect from an inspection of the file and user input
        Raises:
            - EOFError if manual inspection of the file determines that it is empty.
    """

    if infiles[0] == '-':
        dialect = override_dialect(Dialect, delimiter, quoting, quotechar, has_header)
    else:
        for infile in infiles:
            my_file = file_type.FileTyper(infile)
            try:
                dialect = my_file.analyze_file()
                dialect = override_dialect(dialect, delimiter, quoting, quotechar, has_header)
                break
            except file_type.IOErrorEmptyFile:
                continue
        else:
            raise EOFError

    return dialect



def override_dialect(dialect: Dialect,
                     delimiter: Optional[str],
                     quoting: Optional[str],
                     quotechar: Optional[str],
                     has_header: Optional[bool]) -> Dialect:
    """ Consolidates individual dialect fields with a csv Dialect structure.

        Most commonly used by entry points / scripts to combine explicit csv dialect fields
        provided by a user with the dialect returned by inspection of the file.  This is
        sometimes needed if the sniffing/inspection is wrong.  But it is generally not provided
        by the user and so these values will usually be None.
    """

    dialect.delimiter  = delimiter or dialect.delimiter

    if quoting:
        dialect.quoting = file_type.get_quote_number(quoting) if quoting else dialect.quoting
    elif dialect.quoting:
        pass
    else:
        dialect.quoting = file_type.get_quote_number('quote_none')

    dialect.quotechar  = quotechar or dialect.quotechar

    try:
        dialect.has_header = has_header if has_header is not None else dialect.has_header
    except AttributeError:
        dialect.has_header = False

    dialect.lineterminator = '\n'

    return dialect

