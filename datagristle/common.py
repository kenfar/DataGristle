#!/usr/bin/env python
""" Used to hold all common  general-purpose functions and classes

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
import argparse
import errno
import logging
import csv
import inspect
import logging
import math
from os.path import isdir, isfile, exists
from os.path import join as pjoin
from pprint import pprint as pp
import sys
import traceback
from typing import List, Dict, Any, Optional, Tuple, Union, NoReturn

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


def abort(summary: str,
          details: Optional[Any] = None,
          rc: int = 1,
          verbosity: str = 'normal') -> NoReturn:
    """ Creates formatted error message within a box of = characters
        then exits.
    """
    def print_solid_line():
        print('=' * 79, file=sys.stderr)

    def print_empty_line():
        print('= ', end='', file=sys.stderr)
        print(' ' * 75, end='', file=sys.stderr)
        print(' =', file=sys.stderr)

    def print_text_line(text:str):
        for line_num in range(int(math.ceil(len(text)/75))):
            line_start = line_num * 75
            line_end = line_start + 75
            print('= ', end='', file=sys.stderr)
            print(f'{text[line_start:line_end]:<75}', end='', file=sys.stderr)
            print(' =', file=sys.stderr)

    print('', file=sys.stderr)
    print_solid_line()

    print_text_line(summary)
    print_empty_line()

    if details:
        if isinstance(details, str):
            text = details
        else:
            text = repr(details)
        for text_line in text.split('\n'):
            print_text_line(text_line)
            print_empty_line()

    print_empty_line()
    print_text_line('Provide option --help or --long-help for usage information')
    print_empty_line()
    print_solid_line()

    if verbosity == 'debug':
        print(' ', file=sys.stderr)
        traceback.print_stack(file=sys.stderr)

    try:
        logger.critical(summary)      # type: ignore
        if details:
            logger.critical(details)  # type: ignore
    except NameError:
        pass

    sys.exit(rc)



def get_tracepath():
    try:
        curframe = inspect.currentframe()
        curframe = inspect.getouterframes(curframe, 2)
        funcs = [x.function for x in reversed(curframe)
                 if x.function not in ('<module>', 'get_tracepath')]
        tracepath = '-->'.join(funcs)
    except:
        tracepath = '' # could fail if run on pypy, jython, etc
    return tracepath



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
    except KeyError as err:
        raise KeyError(f'Column name not found in colname list: {repr(err)}')

    # extra edit to look for offsets not found within a colname listing:
    if colname_lookup:
        for x in result:
            if x >= colname_lookup_len:
                raise KeyError('column number %s not found in colname list' % x)

    return result



def get_best_col_names(config: Dict[str, Any],
                       dialect) -> Optional[List[str]]:

    if not dialect.has_header:
        return config['col_names']

    if config.get('col_names'):
        return config['col_names']

    # lets now try to get them from the header:
    col_names = None
    infile = 0
    for infile_number in range(len(config['infiles'])):
        col_names = get_col_names_from_header(config['infiles'][infile_number], dialect)
        if col_names:
            return col_names
    else:
        return None


def get_col_names_from_header(file1_fqfn: str,
                              dialect: csv.Dialect) -> List[str]:
    try:
        with open(file1_fqfn, newline='') as f:
            reader = csv.reader(f, dialect=dialect)
            header = reader.__next__()
        col_names = [x.lower().replace(' ', '_') for x in header]
        return col_names
    except StopIteration:
        return None
