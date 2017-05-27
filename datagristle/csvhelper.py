#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011, 2017 Ken Farmer
"""

#--- standard modules ------------------
import csv
from pprint import pprint
from typing import List, Dict, Any, Union, Optional

#--- datagristle modules ------------------
import datagristle.common as comm



def get_quote_number(quote_name: str):
    """ used to help applications look up quote names typically provided by users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
        Note that if a quote_number is accidently passed to this function, it
        will simply pass it through.
    """
    if not comm.isnumeric(quote_name):
        return csv.__dict__[quote_name.upper()]
    elif get_quote_name(quote_name):
        return int(quote_name)
    else:
        raise ValueError('Invalid quote_name: %s' % quote_name)



def get_quote_name(quote_number: int) -> str:
    """ used to help applications look up quote numbers typically provided by
        users.
    """
    for key, value in csv.__dict__.items():
        if value == quote_number:
            return key


def create_dialect(delimiter: str,
                   quoting: int,
                   hasheader: bool,
                   quotechar: str='"',
                   escapechar: Optional[str]=None,
                   skipinitialspace: bool=False,
                   lineterminator: str='\n',
                   validate: bool=False) -> csv.Dialect:
    """ Constructs a csv dialect object from csv attributes.
    """
    dialect                  = csv.Dialect
    dialect.delimiter        = delimiter
    dialect.skipinitialspace = skipinitialspace

    if quoting not in [csv.QUOTE_NONE, csv.QUOTE_MINIMAL, csv.QUOTE_ALL,
                       csv.QUOTE_NONNUMERIC]:
        raise ValueError('Invalid quoting value: %s' % quoting)

    dialect.quoting          = quoting
    dialect.quotechar        = quotechar
    dialect.has_header       = hasheader
    dialect.lineterminator   = lineterminator
    return dialect




