#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

from __future__ import division

#--- standard modules ------------------
import collections
import csv
import os
from pprint import pprint

#--- datagristle modules ------------------
import common as comm

QUOTE_NONE       = csv.QUOTE_NONE
QUOTE_MINIMAL    = csv.QUOTE_MINIMAL
QUOTE_NONNUMERIC = csv.QUOTE_NONNUMERIC
QUOTE_ALL        = csv.QUOTE_ALL

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
    if not comm.isnumeric(quote_name):
        return csv.__dict__[quote_name.upper()]
    elif get_quote_name(quote_name):
        return int(quote_name)
    else:
        raise ValueError, 'Invalid quote_name: %s' % quote_name

def get_quote_name(quote_number):
    """ used to help applications look up quote numbers typically provided by
        users.
    """
    for key, value in csv.__dict__.items():
        if value == quote_number:
            return key


def create_dialect(delimiter,
                   quoting,
                   hasheader,
                   quotechar='"',
                   escapechar=None,
                   skipinitialspace=False,
                   lineterminator='\n',
                   validate=False):
    """ Constructs a csv dialect object from csv attributes.
    """
    dialect                  = csv.Dialect
    dialect.delimiter        = delimiter
    dialect.skipinitialspace = skipinitialspace

    if quoting not in [csv.QUOTE_NONE, csv.QUOTE_MINIMAL, csv.QUOTE_ALL,
                       csv.QUOTE_NONNUMERIC]:
        raise ValueError, 'Invalid quoting value: %s' % quoting
    dialect.quoting          = quoting

    dialect.quotechar        = quotechar
    dialect.has_header       = hasheader
    dialect.lineterminator   = lineterminator
    return dialect




