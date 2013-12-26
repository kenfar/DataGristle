#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldTyper   - class runs all checks on all fields
      get_field_type()
      _get_type()
      is_timestamp() - determines if arg is a timestamp of some type
      is_float()   - determines if arg is a float
      is_integer() - determines if arg is an integer
      is_string()  - determines if arg is a string
    Todo:
      - change get_types to consider whatever has 2 STDs
      - replace get_types freq length logic with something that says, if all
        types are basically numeric, choose float
      - consistency metric
      - leverage list comprehensions more
      - change returned data format to be based on field

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""
from __future__ import division
import datetime
import collections
import math
#import pprint


#--- CONSTANTS -----------------------------------------------------------

MAX_FREQ_SIZE          = 10000         # limits entries within freq dictionaries
DATE_MIN_EPOCH_DEFAULT = 315561661     # 1980-01-01 01:01:01  # (not actual min)
DATE_MAX_EPOCH_DEFAULT = 1893484861    # 2030-01-01 01:01:01  # (not acutal max)
DATE_MAX_LEN           = 26
DATE_INVALID_CHARS = ['`','`','!','@','#','$','%','^','&','*','(',')',
                      '_','+','=','[','{','}','}','|',
                      ';','"',"'",'<','>','?',
                      'q','z','x']
DATE_FORMATS = [ # <scope>, <pattern>, <format>
                ("year",   "YYYY",           "%Y"),
                ("month",  "YYYYMM",         "%Y%m"),
                ("month",  "YYYY-MM",        "%Y-%m"),
                ("month",  "YYYYMM",         "%Y%m"),
                ("day",    "YYYYMMDD",       "%Y%m%d"),
                ("day",    "YYYY-MM-DD",     "%Y-%m-%d"),
                ("day",    "DD/MM/YY",       "%d/%m/%y"),
                ("day",    "DD-MM-YY",       "%d-%m-%y"),
                ("day",    "MM/DD/YY",       "%m/%d/%y"),
                ("day",    "MM-DD-YY",       "%m-%d-%y"),
                ("day",    "MM/DD/YYYY",     "%m/%d/%Y"),
                ("day",    "MM-DD-YYYY",     "%m-%d-%Y"),
                ("day",    "DD/MM/YYYY",     "%d/%m/%Y"),
                ("day",    "DD-MM-YYYY",     "%d-%m-%Y"),
                ("day",    "MON DD,YYYY",    "%b %d,%Y"),
                ("day",    "MON DD, YYYY",   "%b %d, %Y"),
                ("day",    "MONTH DD,YYYY",  "%B %d,%Y"),
                ("day",    "MONTH DD, YYYY", "%B %d, %Y"),
                ("day",    "DD MON,YYYY",    "%d %b,%Y"),
                ("day",    "DD MON, YYYY",   "%d %b, %Y"),
                ("day",    "DD MONTH,YYYY",  "%d %B,%Y"),
                ("day",    "DD MONTH, YYYY", "%d %B, %Y"),
                ("hour",   "YYYY-MM-DD HH",  "%Y-%m-%d %H"),
                ("hour",   "YYYY-MM-DD-HH",  "%Y-%m-%d-%H"),
                ("minute", "YYYY-MM-DD HH:MM", "%Y-%m-%d %H:%M"),
                ("minute", "YYYY-MM-DD-HH.MM", "%Y-%m-%d-%H.%M"),
                ("second", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
                ("second", "YYYY-MM-DD-HH.MM.SS", "%Y-%m-%d-%H.%M.%S"),
                # ".<microsecond>" at end is manually handled below
                ("microsecond", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S") ]




def get_field_type(values):
    """ Determines the type of every item in the value list or dictionary,
        then consolidates that into a single output type.  This is used to 
        determine what type to convert an entire field into - often within
        a database.

        Input 
         - a list or dictionary of strings

        Output:
         - a single value what type the data can be safetly converted into.

        Types identified (and returned) include:
          - unknown
          - string
          - integer
          - float
          - timestamp

        Test Coverage:
          - complete via test harness
    """
    type_freq  = collections.defaultdict(int)

    # count occurances of each type:
    for key in values:
        i = _get_type(key)
        if i != 'unknown':                   # NOTE: unknown is filtered out
            try:                             # values is a dict
                type_freq[i] += values[key]
            except TypeError:                # values is a list
                type_freq[i] += 1
    type_list = type_freq.keys()

    # try simple rules:
    result = _get_field_type_rule(type_list)
    if result:
        return result

    # try probabilities:
    result = _get_field_type_probability(type_freq)
    return (result or 'unknown')



def _get_type(value):
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
    dtc_status, dummy, dummy  = is_timestamp(value)
    if dtc_status:
        return 'timestamp'
    elif is_unknown(value):
        return 'unknown'
    elif is_float(value):
        return 'float'
    elif is_integer(value):
        return 'integer'
    elif is_string(value):
        return 'string'
    else:
        return 'string'


def _get_field_type_rule(type_list):
    """ The intent is to resolve type determinations through simplistic
        rules:
        Additional Notes to consider:
        1. Note that type of 'unknown' must not be included within type_list
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
    assert 'unknown' not in type_list

    # floats with nothing to the right of the decimal point may be ints
    float_set_2i     = set(['integer', 'float'])
    # some floats fall into the timestamp epoch range:
    float_set_2t     = set(['float', 'timestamp'])
    # or a mix of the above two:
    float_set_3      = set(['integer', 'float', 'timestamp'])
    # some integers also fall into the timestamp epoch range:
    integer_set_2t   = set(['integer', 'timestamp'])

    type_set  = set(type_list)

    if len(type_list) == 0:
        return 'unknown'
    elif len(type_list)  == 1:
        field_type = type_list[0]
        return field_type
    elif len(type_list) == 2:
        if not type_set.symmetric_difference(float_set_2i):
            return 'float'
        elif not type_set.symmetric_difference(float_set_2t):
            return 'float'
        elif not type_set.symmetric_difference(integer_set_2t):
            return 'integer'
    elif len(type_list) == 3:
        if not type_set.symmetric_difference(float_set_3):
            return 'float'
    else:
        return None


def _get_field_type_probability(type_freq):
    """ Determines type of field based on the type of the vast majority of
        values.
    """
    total = sum(type_freq.itervalues())

    # if the sample-size is too small, then we can't be sure:
    if total < 10:
        return 'unknown'

    type_pct  = collections.defaultdict(int)
    for key in type_freq:
        type_pct[key] = type_freq[key] / total

    for key in type_pct:
        if type_pct[key] >= 0.95:
            return key

    # no clear winner, we can't be sure:
    return 'unknown'



def is_string(value):
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



def is_integer(value):
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
        i            = float(value)
        fract, dummy = math.modf(i)
        if fract > 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_float(value):
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
        i            = float(value)
        fract, dummy = math.modf(i)
        if fract == 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_unknown(value):
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
        Test coverage:
          - complete, via test harness
    """
    unk_vals = ['na', 'n/a', 'unk', 'unknown', '']
    try:
        if value.strip().lower() in unk_vals:
            return True
        else:
            return False
    except AttributeError:
        return False
    except TypeError:
        return False


def is_timestamp(time_str):
    """ Determine if arg is a timestamp and if so what format

        Args:
           time_str - character string that may be a date, time, epoch or combo
        Returns:
           status   - True if date/time False if not
           scope    - kind of timestamp
           pattern  - date mask

        To do:
           - consider overrides to default date min & max epoch limits
           - consider consolidating epoch checks with rest of checks
    """
    non_date = (False, None, None)
    if len(time_str) > DATE_MAX_LEN:
        return non_date

    try:
        float_str = float(time_str)
        if DATE_MIN_EPOCH_DEFAULT < float_str < DATE_MAX_EPOCH_DEFAULT:
            t_date = datetime.datetime.fromtimestamp(float(time_str))
            return True, 'second', 'epoch'
    except ValueError:
        pass

    for scope, pattern, date_format in DATE_FORMATS:
        if scope == "microsecond":
            # Special handling for microsecond part. AFAIK there isn't a
            # strftime code for this.
            if time_str.count('.') != 1:
                continue
            time_str, microseconds_str = time_str.split('.')
            try:
                microsecond = int((microseconds_str + '000000')[:6])
            except ValueError:
                continue
        try:
            t_date = datetime.datetime.strptime(time_str, date_format)
        except ValueError:
            pass
        else:
            if scope == "microsecond":
                t_date = t_date.replace(microsecond=microsecond)
            return True, scope, pattern
    else:
        return False,  None, None



