#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldTyper   - class runs all checks on all fields
      get_field_type()
      is_timestamp() - determines if arg is a timestamp of some type
      is_float()   - determines if arg is a float
      is_integer() - determines if arg is an integer
      is_string()  - determines if arg is a string
    Todo:
      - change get_types to consider whatever has 2 STDs
      - replace get_types freq length logic with something that says, if all
        types are basically numeric, choose float
      - consistency metric
      - change returned data format to be based on field

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017,2022 Ken Farmer
"""
import datetime
import math
from pprint import pprint as pp
import re
from typing import Any, List, Tuple, Dict, Optional, Union


#--- CONSTANTS -----------------------------------------------------------

GRISTLE_FIELD_TYPES = ['unknown', 'string', 'float', 'integer', 'timestamp']
MAX_TYPE_SIZE = 1000
DATE_MIN_LEN = 8
DATE_MAX_LEN = 31 # supports iso8601 with microseconds and timezone
NON_MICROSECOND_FORMATS = [
    ("day", "YYYY-MM-DD", "%Y-%m-%d"),
    ("day", "DD/MM/YY", "%d/%m/%y"),
    ("day", "DD-MM-YY", "%d-%m-%y"),
    ("day", "MM/DD/YY", "%m/%d/%y"),
    ("day", "MM-DD-YY", "%m-%d-%y"),
    ("day", "MM/DD/YYYY", "%m/%d/%Y"),
    ("day", "MM-DD-YYYY", "%m-%d-%Y"),
    ("day", "DD/MM/YYYY", "%d/%m/%Y"),
    ("day", "DD-MM-YYYY", "%d-%m-%Y"),
    ("day", "MON DD,YYYY", "%b %d,%Y"),
    ("day", "MON DD, YYYY", "%b %d, %Y"),
    ("day", "MONTH DD,YYYY", "%B %d,%Y"),
    ("day", "MONTH DD, YYYY", "%B %d, %Y"),
    ("day", "DD MON,YYYY", "%d %b,%Y"),
    ("day", "DD MON, YYYY", "%d %b, %Y"),
    ("day", "DD MONTH,YYYY", "%d %B,%Y"),
    ("day", "DD MONTH, YYYY", "%d %B, %Y"),
    ("hour", "YYYY-MM-DDTHH", "%Y-%m-%dT%H"),
    ("hour", "YYYY-MM-DD HH", "%Y-%m-%d %H"),
    ("hour", "YYYY-MM-DD-HH", "%Y-%m-%d-%H"),
    ("minute", "YYYY-MM-DDTHH:MM", "%Y-%m-%dT%H:%M"),
    ("minute", "YYYY-MM-DD HH:MM", "%Y-%m-%d %H:%M"),
    ("minute", "YYYY-MM-DD-HH:MM", "%Y-%m-%d-%H:%M"),
    ("second", "YYYY-MM-DDTHH:MM:SS", "%Y-%m-%dT%H:%M:%S"),
    ("second", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
    ("second", "YYYY-MM-DD-HH:MM:SS", "%Y-%m-%d-%H:%M:%S")]
MICROSECOND_FORMATS = [
    ("microsecond", "YYYY-MM-DDTHH:MM:SS", "%Y-%m-%dT%H:%M:%S"),
    ("microsecond", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
    ("microsecond", "YYYY-MM-DD-HH:MM:SS", "%Y-%m-%d-%H:%M:%S")]
INVALID_TIMESTAMP_SYMBOL_REGEX = re.compile('[`~!@#$%^&*()_={}[]|\\;\'\"<>?]')


def get_field_type(values: Dict[str, int]) -> str:
    """ Determines the type of every item in the value list or dictionary,
        then consolidates that into a single output type.  This is used to
        determine what type to convert an entire field into - often within
        a database.

        Input
         - a list or dictionary of strings

        Output:
         - a single value what type the data can be safely converted into.

        Types identified (and returned) include:
          - unknown
          - string
          - integer
          - float
          - timestamp
    """
    if values is None:
        return 'unknown'

    type_freq: Dict[str, int] = {}

    type_freq = _get_type_freq_from_dict(values)

    clean_type_list = [x for x in type_freq if x != 'unknown']

    result = _get_field_type_rule(clean_type_list)
    if result:
        return result

    return _get_field_type_probability(type_freq) or 'unknown'


def _get_type_freq_from_dict(values: Dict):
    type_freq: Dict[str, int] = {}

    # Truncate super-long lists: 10k or so should be enough to sample data
    values = list(values.items())[:MAX_TYPE_SIZE]

    for key, count in values:
        key_type = _get_type(key)
        try:
            type_freq[key_type] += int(count)
        except KeyError:
            type_freq[key_type] = int(count)
    return type_freq



def _get_type(value: Any) -> str:
    """ accepts a single string value and returns its potential type

        Types identified (and returned) include:
          - unknown
          - string
          - number
          - integer
          - float
          - timestamp

        Test Coverage:
          - complete via test harness
    """
    #dtc_status, _, _ = is_timestamp(value)
    #if dtc_status:
    #    return 'timestamp'
    if is_unknown(value):
        return 'unknown'
    elif is_float(value):
        return 'float'
    elif is_integer(value):
        return 'integer'
    elif is_timestamp(value):
        return 'timestamp'
    elif is_string(value):
        return 'string'
    else:
        return 'string'



def _get_field_type_rule(types: List[str]) -> Optional[str]:
    """ The intent is to resolve type determinations through simplistic
        rules:
        Additional Notes to consider:
        1. Note that type of 'unknown' must not be included within types
        2. empty list = unknown
        3. one-item list = that item
        4. 2-3 item list of number types = float
        5. timestamps include epochs - which look like any integer or float.
           Because of this a mix of timestamps + floats/integers will be considered
           a float or integer.
        Challenge is in handling data quality problems - like the documented
        case in which a file with 8000 timestamps in the yyyy-mm-dd have 4 records
        with floats.   These floats should have been kicked out as garbage data -
        but if the timestamps were epochs then that would not be appropriate.
    """
    assert 'unknown' not in types

    # floats with nothing to the right of the decimal point may be ints
    float_set_2i = set(['integer', 'float'])
    # some floats fall into the timestamp epoch range:
    float_set_2t = set(['float', 'timestamp'])
    # or a mix of the above two:
    float_set_3 = set(['integer', 'float', 'timestamp'])
    # some integers also fall into the timestamp epoch range:
    integer_set_2t = set(['integer', 'timestamp'])

    type_set = set(types)

    result = None
    if len(types) == 0:
        result = 'unknown'
    elif len(types) == 1:
        result = types[0]
    elif len(types) == 2:
        if not type_set.symmetric_difference(float_set_2i):
            result = 'float'
        elif not type_set.symmetric_difference(float_set_2t):
            result = 'float'
        elif not type_set.symmetric_difference(integer_set_2t):
            result = 'integer'
    elif len(types) == 3:
        if not type_set.symmetric_difference(float_set_3):
            result = 'float'
    return result



def _get_field_type_probability(type_freq) -> str:
    """ Determines type of field based on the type of the vast majority of
        values.
    """
    total = sum(type_freq.values())
    type_pct = {x:type_freq[x]/total for x in type_freq}

    if total < 10:
        return 'unknown'

    for key in type_pct:
        if type_pct[key] >= 0.95:
            return key
    else:
        return 'unknown'



def is_string(value: Any) -> bool:
    """ Returns True if the value is a string, subject to false-negatives
        if the string is all numeric.
        'b'      is True
        ''       is True
        ' '      is True
        '$3'     is True
        '4,333'  is True
        '33.22'  is False
        '3'      is False
        '-3'     is False
        3        is False
        3.3      is False
        None     is False
        Test coverage:
          - complete, via test harness
    """
    try:                    # catch integers & floats
        float(value)
        return False
    except TypeError:       # catch None
        return False
    except ValueError:      # catch characters
        return True



def is_integer(value: Any) -> bool:
    """ Returns True if the input consists soley of digits and represents an
        integer rather than character data or a float.
        '3'       is True
        '-3'      is True
        3         is True
        -3        is True
        3.3       is False
        '33.22'   is False
        '4,333'   is False
        '$3'      is False
        ''        is False
        'b'       is False
        None      is False
        Test coverage:
          - complete, via test harness
    """
    try:
        i = float(value)
        fract, dummy = math.modf(i)
        if fract > 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_float(value: Any) -> bool:
    """ Returns True if the input consists soley of digits and represents a
        float rather than character data or an integer.
        44.55   is True
        '33.22' is True
        6       is False
        '3'     is False
        '-3'    is False
        '4,333' is False
        '$3'    is False
        ''      is False
        'b'     is False
        None    is False
        Test coverage:
          - complete, via test harness
    """
    try:
        i = float(value)
        fract, dummy = math.modf(i)
        if fract == 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_unknown(value: Any) -> bool:
    """ Returns True if the value is a common unknown indicator:
        ''        is True
        ' '       is True
        'na'      is True
        'NA'      is True
        'n/a'     is True
        'N/A'     is True
        'unk'     is True
        'unknown' is True
        '3'       is False
        '-3'      is False
        '33.22'   is False
        '4,333'   is False
        '$3'      is False
        'b'       is False
        3         is False
        3.3       is False
        None      is False
    """
    unk_vals = ['na', 'n/a', 'unk', 'unknown', '']
    try:
        return value.strip().lower() in unk_vals
    except AttributeError:
        return False
    except TypeError:
        return False



def is_timestamp(time_val: Union[float, str]) -> bool:
    """ Determine if arg is a timestamp and if so what format

    Args:
        time_val - normally a string, but could be a float
    Returns:
        status   - True if date/time False if not

    To do:
        - consider overrides to default date min & max epoch limits
    """

    if isinstance(time_val, float):
        return False
    if len(time_val) > DATE_MAX_LEN:
        return False
    if len(time_val) < 8: #DATE_MIN_LEN:
        return False

    if INVALID_TIMESTAMP_SYMBOL_REGEX.match(time_val):
        return False

    # remove timezones:
    if time_val.endswith('z') or time_val.endswith('Z'):
        time_val = time_val[:-1]
    parts = time_val.split('+')
    if parts:
        time_val = parts[0]
    if len(time_val) > 14:
        dash_offset = time_val.rfind('-')
        if dash_offset > 11:
            time_val = time_val[:dash_offset]


    if '.' in time_val:
        time_val = time_val.split('.')[0]
        for scope, _, date_format in MICROSECOND_FORMATS:
            try:
                t_date = datetime.datetime.strptime(time_val, date_format)
            except ValueError:
                pass
            else:
                return True
        else:
            return False
    else:
        for scope, _, date_format in NON_MICROSECOND_FORMATS:
            try:
                t_date = datetime.datetime.strptime(time_val, date_format)
            except ValueError:
                pass
            else:
                return True
        else:
            return False

