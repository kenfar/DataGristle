#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011, 2017 Ken Farmer
"""

import csv
from typing import Optional



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
