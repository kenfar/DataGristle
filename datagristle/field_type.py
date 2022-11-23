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
ONLY_NUMBERS_REGEX = re.compile("[0-9]+")


class FieldType:

    def __init__(self,
                 values: List[Tuple[Any, int]]) -> None:

        self.values = list(values)
        self.type_freq: Dict[str, int] = {}
        self.clean_type_values: List[Tuple] = []
        self.result: str = 'unknown'


    def get_field_type(self) -> str:
        if self.values is None:
            return 'unknown'

        self._get_type_freq_from_dict()

        self.clean_type_values = [x for x in self.type_freq if x != 'unknown']

        self._get_field_type_rule()
        if self.result == 'unknown':
            self._get_field_type_probability() or 'unknown'
        return self.result


    def _get_type_freq_from_dict(self):

        for key, count in self.values[:MAX_TYPE_SIZE]:
            key_type = self._get_type(key)
            try:
                self.type_freq[key_type] += int(count)
            except KeyError:
                self.type_freq[key_type] = int(count)


    def _get_type(self,
                  value: Any) -> str:
        """ accepts a single string value and returns its potential type

            Types identified (and returned) include:
            - unknown
            - string
            - number
            - integer
            - float
            - timestamp
        """
        if is_unknown(value):
            return 'unknown'
        elif is_float(value):
            return 'float'
        elif is_integer(value):
            return 'integer'
        elif self._is_timestamp(value):
            return 'timestamp'
        else:
            return 'string'


    def _get_field_type_rule(self) -> Optional[str]:
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
        # floats with nothing to the right of the decimal point may be ints
        float_set_2i = set(['integer', 'float'])

        type_set = set(self.clean_type_values)

        if len(self.clean_type_values) == 0:
            self.result = 'unknown'
        elif len(self.clean_type_values) == 1:
            self.result = self.clean_type_values[0]
        elif len(self.clean_type_values) == 2:
            if not type_set.symmetric_difference(float_set_2i):
                self.result = 'float'



    def _get_field_type_probability(self) -> str:
        """ Determines type of field based on the type of the vast majority of
            values.
        """
        total = sum(self.type_freq.values())
        for key in self.type_freq:
           if self.type_freq[key]/total >= 0.8:
               self.result = key



    def _is_timestamp(self,
                     time_val: Union[float, str]) -> bool:
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

        numbers = ONLY_NUMBERS_REGEX.findall(time_val)
        if len(numbers) <= 1:
            return False
        if len(numbers) > 3:
            return False
        number_length = len(''.join(numbers))
        if 3 > number_length > 8:
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
    """
    try:
        int(value)
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
    """
    try:
        float(value)
        try:
           int(value)
           return False
        except ValueError:
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


