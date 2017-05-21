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
    Copyright 2011,2012,2013 Ken Farmer
"""
import collections
import csv

import datagristle.field_type as typer
from typing import List


#--- CONSTANTS -----------------------------------------------------------

MAX_FREQ_SIZE_DEFAULT  = 1000000     # limits entries within freq dictionaries


def get_field_names(filename: str,
                    dialect,
                    col_number=None) -> List[str]:
    """ Determines names of fields
        Inputs:
        Outputs:
        Misc:
          - if the file is empty it will return None
    """
    reader = csv.reader(open(filename, 'r'), dialect=dialect)
    for field_names in reader:
        break
    else:
        return None

    if col_number is None:       # get names for all fields
        final_names = []
        for col_sub in range(len(field_names)):
            if dialect.has_header:
                final_names.append(field_names[col_sub].strip())
            else:
                final_names.append('field_%d' % col_sub)
        return final_names
    else:                        # get name for single field
        final_name = ''
        if dialect.has_header:
            final_name = field_names[col_number].strip()
        else:
            final_name = 'field_%d' % col_number
        return final_name




def get_case(field_type, values):
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
        Test coverage:
          - complete, via test harness
    """
    freq = collections.defaultdict(int)
    case = None

    if field_type != 'string':
        return 'n/a'

    # count occurances of each case field_type in values:
    for key in values:
        if typer.is_unknown(key):
            freq['unk']    += 1
        elif typer.is_integer(key):     # will be ignoring these
            freq['number'] += 1
        elif typer.is_float(key):       # will be ignoring these
            freq['number'] += 1
        elif key.islower():
            freq['lower'] += 1
        elif key.isupper():
            freq['upper'] += 1
        else:
            freq['mixed'] += 1

    # evaluate frequency distribution:
    if 'mixed' in freq:
        case = 'mixed'
    elif ('lower' in freq and 'upper' not in freq):
        case = 'lower'
    elif ('lower' not in freq and 'upper' in freq):
        case = 'upper'
    elif ('lower' in freq and 'upper' in freq):
        case = 'mixed'
    else:
        case = 'unknown'

    return case



def get_field_freq(filename,
                   dialect,
                   field_number,
                   max_freq_size=MAX_FREQ_SIZE_DEFAULT,
                   read_limit=-1):
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
    freq            = collections.defaultdict(int)
    truncated       = False
    invalid_row_cnt = 0

    row_cnt = 0
    with open(filename, 'rt') as infile:
        reader = csv.reader(infile, dialect)
        for fields in reader:
            row_cnt += 1
            if row_cnt == 1 and dialect.has_header:
                continue
            try:
                freq[fields[field_number].strip()] += 1
            except IndexError:
                invalid_row_cnt += 1
            if max_freq_size > -1 and len(freq) >= max_freq_size:
                print('      WARNING: freq dict is too large - will trunc')
                truncated = True
                break
            elif read_limit > -1 and row_cnt >= read_limit:
                truncated = True
                break

    return freq, truncated, invalid_row_cnt



def get_min(value_type, values):
    """ Returns the minimum value of the input.  Ignores unknown values, if
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single minimum value of the appropriate type

        Test Coverage:
          - complete via test harness

    """
    assert value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None]

    known_vals = []
    for val in values:
        if not typer.is_unknown(val):
            try:
                if value_type == 'integer':
                    known_vals.append(int(val))
                elif value_type == 'float':
                    known_vals.append(float(val))
                else:
                    known_vals.append(val)
            except ValueError:
                pass                       # ignore invalid values

    # next return the minimum value
    try:
        return str(min(known_vals))
    except ValueError:
        return None



def get_max(value_type, values):
    """ Returns the maximum value of the input.  Ignores unknown values, if
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single maximum value of the appropriate type

        Test Coverage:
          - complete via test harness

    """
    assert value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None]

    known_vals = []
    for val in values:
        if not typer.is_unknown(val):
            try:
                if value_type == 'integer':
                    known_vals.append(int(val))
                elif value_type == 'float':
                    known_vals.append(float(val))
                else:
                    known_vals.append(val)
            except ValueError:
                pass                       # ignore invalid values

    try:
        return str(max(known_vals))
    except ValueError:
        return None



def get_max_length(values):
    """ Returns the maximum length value of the input.   If
        no values found besides unknown it will just return 'None'

        Inputs:
          - dictionary or list of string values
        Outputs:
          - the single maximum value
    """
    max_length = 0

    for value in values:
        if not typer.is_unknown(value):
            if len(value) > max_length:
                max_length = len(value)

    return max_length



def get_min_length(values):
    """ Returns the minimum length value of the input.   If
        no values found besides unknown it will just return 999999

        Inputs:
          - dictionary or list of string values
        Outputs:
          - the single minimum value
    """
    min_length = 999999

    for value in values:
        if not typer.is_unknown(value):
            if len(value) < min_length:
                min_length = len(value)

    return min_length




