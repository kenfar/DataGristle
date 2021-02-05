#!/usr/bin/env python
""" Used to hold all common  general-purpose functions and classes

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
import sys
import argparse
import logging
import math
import errno
import csv
from os.path import isdir, isfile, exists
from os.path import join as pjoin
from typing import List, Dict, Any, Optional, Tuple, Union

from datagristle._version import __version__


FreqType = List[Tuple[Any, int]]
StrFreqType = List[Tuple[str, int]]
NumericFreqType = List[Tuple[Union[int, float], int]]


def isnumeric(number: Any) -> bool:
    """ Tests whether or not the input is numeric.
        Args:
           - number:  a string containing a number that may be either an integer
             or a float, a positive or a negative or zero.
        Returns:  True or False
    """
    try:
        float(number)
        return True
    except (TypeError, ValueError):
        return False


def get_common_key(count_dict: Dict[Any, Union[int, float]]) -> Tuple[Any, float]:
    """  Provides the most common key in a dictionary as well as its frequency
         expressed as a percentage.  For example:
         cd = ['car':    7
               'boat':  30
               'truck':  8
               'plane':  5
         print most_common_key(cd)
         >>> boat, 60
    """
    sorted_keys  = (sorted(count_dict, key=count_dict.get))
    total_values = sum(count_dict.values())
    most_common_key       = sorted_keys[-1]
    most_common_key_value = count_dict[sorted_keys[-1]]
    most_common_pct       = most_common_key_value / total_values  # type: ignore
    return most_common_key, most_common_pct


def coalesce(default: Any, *args: Any) -> Any:
    """ Returns the first non-None value.
        If no non-None args exist, then return default.
    """
    for arg in args:
        if arg not in (None, "'None'", 'None'):
            return arg
    return default


def dict_coalesce(struct: Dict, key: Any, default: Any=None) -> Any:
    try:
        return struct[key]
    except KeyError:
        return default


def ifprint(value: Any, string: str, *args: Any) -> None:
    if value is not None:
        print(string % args)



class DelimiterAction(argparse.Action):
    """ An argparse delimiter action to fix unprintable delimiter values.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        val = dialect_del_fixer(values)
        setattr(namespace, self.dest, val)



def dialect_del_fixer(values: str) -> str:
    """ Fix unprintable delimiter values provided as CLI args
    """
    if values == '\\t':
        val = '\t'
    elif values == 'tab':
        val = '\t'
    elif values == '\\n':
        val = '\n'
    else:
        val = values
    return val


def abort(summary: str, details: Optional[str] = None, rc: int = 1) -> None:
    """ Creates formatted error message within a box of = characters
        then exits.
    """
    print('=' * 79)

    print('=== ', end='')
    print('%-71.71s' % summary, end='')
    print(' ===')

    if details:
        for i in range(int(math.ceil(len(details)/68))):
            print('=== ', end='')
            print('%-71.71s' % details[i*68:(i*68)+68], end='')
            print(' ===')
    print('=' * 79)

    try:
        logger.critical(summary)
        if details:
            logger.critical(details)
    except NameError:
        pass

    sys.exit(rc)


def colnames_to_coloff0(col_names: List[str], lookup_list: List[Any]) -> List[int]:
    """ Returns a list of collection column positions with offset of 0 for a list of
        collection column names (optional) and a lookup list of col names and/or col
        offsets.

        Inputs:
           - col_names   - list of collection column names, may be empty
           - lookup_list - list of column names or positions to lookup (off0)
        Returns:
           - result      - list of column positions (off0)
        Raises:
           - KeyError if column name from lookup_list not in colnames,
                      or if col position from lookup_list extends beyond
                      populated col_names list.
        Notes:
           - output will always be a list of integers
           - input column offsets can be integers (0) or strings ('0')
    """
    colname_lookup = dict((element, offset) for offset, element in enumerate(col_names))
    colname_lookup_len = len(colname_lookup)

    try:
        result =  [int(x) if isnumeric(x) else colname_lookup[x] for x in lookup_list]
    except KeyError:
        raise KeyError('Column name not found in colname list')

    # extra edit to look for offsets not found within a colname listing:
    if colname_lookup:
        for x in result:
            if x >= colname_lookup_len:
                raise KeyError('column number %s not found in colname list' % x)

    return result



def get_best_col_names(config: Dict[str, Any],
                       dialect: csv.Dialect) -> Dict[str, Any]:
    if dialect.has_header:
        if len(config['col_names']):
            return config['col_names']
        else:
            return get_col_names_from_header(config['infiles'][0], dialect)
    else:
        return config['col_names']


def get_col_names_from_header(file1_fqfn: str,
                              dialect: csv.Dialect) -> List[str]:
    with open(file1_fqfn, newline='') as f:
        reader = csv.reader(f, dialect=dialect)
        header = reader.__next__()
    col_names = [x.lower().replace(' ', '_') for x in header]
    return col_names



