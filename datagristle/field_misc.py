#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      - get_field_names
      - get_case
      - get_field_freq
      - get_min
      - get_max
      - get_max_length
      - get_min_length

    Todo:
      - get_field_freq()
          - change get_field_rec to better handle files within inconsistent
            number of fields

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
import csv
from typing import List, Union, Dict, Tuple, Any, Optional
from pprint import pprint as pp

import datagristle.field_type as typer
import datagristle.csvhelper as csvhelper
import datagristle.common as common

MAX_FREQ_SIZE_DEFAULT = 1000000     # limits entries within freq dictionaries



def get_field_name(filename: str,
                   dialect: csvhelper.Dialect,
                   col_number: int) -> str:
    """ Determines names of fields
        Inputs:
        Outputs:
        Misc:
          - if the file is empty it will return None
    """
    reader = csv.reader(open(filename, newline=''), dialect=dialect)
    for field_names in reader:
        break
    else:
        raise EOFError

    final_name = ''
    if dialect.has_header:
        final_name = field_names[col_number].strip()
    else:
        final_name = 'field_%d' % col_number
    return final_name



def get_field_names(filename: str,
                    dialect) -> List[str]:
    """ Determines names of fields
        Inputs:
        Outputs:
        Misc:
          - if the file is empty it will return None
    """
    reader = csv.reader(open(filename, newline=''), dialect=dialect)
    for field_names in reader:
        break
    else:
        raise EOFError

    final_names = []
    for col_sub in range(len(field_names)):
        if dialect.has_header:
            final_names.append(field_names[col_sub].strip())
        else:
            final_names.append('field_%d' % col_sub)
    return final_names



def get_case(field_type: str, values: common.StrFreqType) -> str:
    """ Determines the case of a list or dictionary of values.
        Args:
          - type:    if not == 'string', will return 'n/a'
          - values:  could be either dictionary or list.  If it's a list, then
                     it will only examine the keys.
        Returns:
          - one of:  'mixed','lower','upper','unknown'
        Misc notes:
          - "unknown values" are ignored
          - empty values list/dict results in 'unknown' result
        To do:
          - add consistency factor
    """
    case = None

    if field_type != 'string':
        return 'n/a'

    is_unknown = typer.is_unknown
    is_integer = typer.is_integer
    is_float = typer.is_float
    clean_values = [x for x in values if not is_unknown(x[0])
                    and not is_integer(x[0]) and not is_float(x[0])]

    lower_cnt = sum([x[1] for x in clean_values if x[0].islower()])
    upper_cnt = sum([x[1] for x in clean_values if x[0].isupper()])
    mixed_cnt = sum([x[1] for x in clean_values if not x[0].isupper() and not x[0].islower()])

    # evaluate frequency distribution:
    if mixed_cnt:
        case = 'mixed'
    elif lower_cnt and not upper_cnt:
        case = 'lower'
    elif upper_cnt and not lower_cnt:
        case = 'upper'
    elif upper_cnt and lower_cnt:
        case = 'mixed'
    else:
        case = 'unknown'

    return case



def get_field_freq(filename: str,
                   dialect: csvhelper.Dialect,
                   field_number: int,
                   max_freq_size: int = MAX_FREQ_SIZE_DEFAULT,
                   read_limit: int = -1) -> Tuple[Dict[Any, int], bool, int]:
    """ Collects a frequency distribution for a single field by reading the
        file provided.

        Arguments:
            - filename:
            - dialect:
            - field_number:
            - max_freq_size: defaults to the system max, which is typically
              over 1M.  A value of -1 will result in 'no limit'.
            - read_limit:  A performance option that stops reading after this
              number of records.  The default is -1 which means, no limit.

        Returns:
            - freq: a dictionary of values & counts
            - truncated: a boolean that indicates whether or not the results
              were obtained from the entire file, or had to stop due to
              max_freq_size or read_limit.
            - invalid_row_cnt: a count of rows that could not be analyzed,
              because they were missing this field.

        Issues:
            - has limited checking for wrong number of fields in rec
    """
    freq = {}
    truncated = False
    invalid_row_cnt = 0

    row_cnt = 0
    with open(filename, 'rt', newline='') as infile:
        reader = csv.reader(infile, dialect)
        for fields in reader:
            row_cnt += 1
            if row_cnt == 1 and dialect.has_header:
                continue
            try:
                freq[fields[field_number].strip()] += 1
            except KeyError:
                freq[fields[field_number].strip()] = 1
            except IndexError:
                invalid_row_cnt += 1
            except AttributeError as e: # quote_nonnumeric returns floats(!)
                if ("'float' object has no attribute 'strip'")  in repr(e):
                    if fields[field_number] in freq:
                        freq[fields[field_number]] += 1
                    else:
                        freq[fields[field_number]] = 1
            if max_freq_size > -1 and len(freq) >= max_freq_size:
                print('      WARNING: freq dict is too large - will trunc')
                truncated = True
                break
            elif read_limit > -1 and row_cnt >= read_limit:
                truncated = True
                break

    return freq, truncated, invalid_row_cnt



def get_min(value_type: str, values: common.FreqType) -> Optional[str]:
    """ Returns the minimum value of the input.  Ignores unknown values, if
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single minimum value of the appropriate type
    """
    assert value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None]

    if value_type == 'integer':
        myfunc = int
    elif value_type == 'float':
        myfunc = float
    else:
        myfunc = str

    def transform(val):
        try:
            result = myfunc(val)
        except ValueError:
            pass # just drop any invalid data
        else:
            return result

    try:
        minimum = str(min([transform(x[0]) for x in values if not typer.is_unknown(x[0])]))
    except ValueError:
        return None
    else:
        return minimum





def get_max(value_type: str, values: common.FreqType) -> Optional[Any]:
    """ Returns the maximum value of the input.  Ignores unknown values, if
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single maximum value of the appropriate type
    """
    assert value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None]

    if value_type == 'integer':
        myfunc = int
    elif value_type == 'float':
        myfunc = float
    else:
        myfunc = str

    def transform(val):
        try:
            result = myfunc(val)
        except ValueError:
            pass # just drop any invalid data
        else:
            return result

    try:
        maximum = str(max([transform(x[0]) for x in values if not typer.is_unknown(x[0])]))
    except ValueError:
        return None
    else:
        return maximum



def get_max_length(values: common.StrFreqType) -> int:
    """ Returns the maximum length value of the input.   If
        no values found besides unknown it will just return 'None'

        Inputs:
          - dictionary or list of string values
        Outputs:
          - the single maximum value
    """
    max_length = 0
    return max([len(value[0]) for value in values if not typer.is_unknown(value[0])]) or max_length



def get_min_length(values: common.StrFreqType) -> int:
    """ Returns the minimum length value of the input.   If
        no values found besides unknown it will just return 999999

    Inputs:
       - dictionary or list of string values
    Outputs:
       - the single minimum value
    """
    min_length = 999999
    return min([len(value[0]) for value in values if not typer.is_unknown(value[0])]) or min_length
