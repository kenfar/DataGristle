#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldType()             - class runs all checks on all fields
      get_field_type()
      is_timestamp()          - returns True if arg is a timestamp and the format
      is_timestamp_extended() - returns True if arg is a timestamp and the format
      is_float()              - returns True if arg is a float
      is_integer()            - returns True if arg is an integer
      is_string()             - returns True if arg is a string
      is_unknown()            - returns True if arg is a string

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
import datetime
from pprint import pprint as pp
import re
from typing import Any, Optional, Union


#--- CONSTANTS -----------------------------------------------------------

GRISTLE_FIELD_TYPES = ['unknown', 'string', 'float', 'integer', 'timestamp']
MAX_TYPE_SIZE = 1000
DATE_MIN_LEN = 8
DATE_MAX_LEN = 31 # supports iso8601 with microseconds and timezone

# scope, format_name, format, count:
TIMESTAMP_FORMATS = [
    ("day", "YYYY-MM-DD", "%Y-%m-%d", 0),
    ("day", "DD/MM/YY", "%d/%m/%y", 0),
    ("day", "DD-MM-YY", "%d-%m-%y", 0),
    ("day", "MM/DD/YY", "%m/%d/%y", 0),
    ("day", "MM-DD-YY", "%m-%d-%y", 0),
    ("day", "MM/DD/YYYY", "%m/%d/%Y", 0),
    ("day", "MM-DD-YYYY", "%m-%d-%Y", 0),
    ("day", "DD/MM/YYYY", "%d/%m/%Y", 0),
    ("day", "DD-MM-YYYY", "%d-%m-%Y", 0),
    ("day", "MON DD,YYYY", "%b %d,%Y", 0),
    ("day", "MON DD, YYYY", "%b %d, %Y", 0),
    ("day", "MONTH DD,YYYY", "%B %d,%Y", 0),
    ("day", "MONTH DD, YYYY", "%B %d, %Y", 0),
    ("day", "DD MON,YYYY", "%d %b,%Y", 0),
    ("day", "DD MON, YYYY", "%d %b, %Y", 0),
    ("day", "DD MONTH,YYYY", "%d %B,%Y", 0),
    ("day", "DD MONTH, YYYY", "%d %B, %Y", 0),
    ("hour", "YYYY-MM-DDTHH", "%Y-%m-%dT%H", 0),
    ("hour", "YYYY-MM-DD HH", "%Y-%m-%d %H", 0),
    ("hour", "YYYY-MM-DD-HH", "%Y-%m-%d-%H", 0),
    ("minute", "YYYY-MM-DDTHH:MM", "%Y-%m-%dT%H:%M", 0),
    ("minute", "YYYY-MM-DD HH:MM", "%Y-%m-%d %H:%M", 0),
    ("minute", "YYYY-MM-DD-HH:MM", "%Y-%m-%d-%H:%M", 0),
    ("minute", "YYYY-MM-DDTHH:MMz", "%Y-%m-%dT%H:%M%z", 0),
    ("minute", "YYYY-MM-DD-HH:MMz", "%Y-%m-%d-%H:%M%z", 0),
    ("minute", "YYYY-MM-DD HH:MMz", "%Y-%m-%d %H:%M%z", 0),
    ("minute", "YYYY-MM-DDTHH:MMZ", "%Y-%m-%dT%H:%M%Z", 0),
    ("minute", "YYYY-MM-DD-HH:MMZ", "%Y-%m-%d-%H:%M%Z", 0),
    ("minute", "YYYY-MM-DD HH:MMZ", "%Y-%m-%d %H:%M%Z", 0),
    ("second", "YYYY-MM-DDTHH:MM:SS", "%Y-%m-%dT%H:%M:%S", 0),
    ("second", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S", 0),
    ("second", "YYYY-MM-DD-HH:MM:SS", "%Y-%m-%d-%H:%M:%S", 0),
    ("second", "YYYY-MM-DDTHH:MM:SSz", "%Y-%m-%dT%H:%M:%S%z", 0),
    ("second", "YYYY-MM-DD-HH:MM:SSz", "%Y-%m-%d-%H:%M:%S%z", 0),
    ("second", "YYYY-MM-DD HH:MM:SSz", "%Y-%m-%d %H:%M:%S%z", 0),
    ("second", "YYYY-MM-DDTHH:MM:SSZ", "%Y-%m-%dT%H:%M:%S%Z", 0),
    ("second", "YYYY-MM-DD-HH:MM:SSZ", "%Y-%m-%d-%H:%M:%S%Z", 0),
    ("second", "YYYY-MM-DD HH:MM:SSZ", "%Y-%m-%d %H:%M:%S%Z", 0),
    ("microsecond", "YYYY-MM-DDTHH:MM:SS.MS",  "%Y-%m-%dT%H:%M:%S.%f", 0),
    ("microsecond", "YYYY-MM-DD HH:MM:SS.MS",  "%Y-%m-%d %H:%M:%S.%f", 0),
    ("microsecond", "YYYY-MM-DD-HH:MM:SS.MS",  "%Y-%m-%d-%H:%M:%S.%f", 0),
    ("microsecond", "YYYY-MM-DDTHH:MM:SS.MSz", "%Y-%m-%dT%H:%M:%S.%f%z", 0),
    ("microsecond", "YYYY-MM-DD HH:MM:SS.MSz", "%Y-%m-%d %H:%M:%S.%f%z", 0),
    ("microsecond", "YYYY-MM-DD-HH:MM:SS.MSz", "%Y-%m-%d-%H:%M:%S.%f%z", 0),
    ("microsecond", "YYYY-MM-DDTHH:MM:SS.MSZ", "%Y-%m-%dT%H:%M:%S.%f%Z", 0),
    ("microsecond", "YYYY-MM-DD HH:MM:SS.MSZ", "%Y-%m-%d %H:%M:%S.%f%Z", 0),
    ("microsecond", "YYYY-MM-DD-HH:MM:SS.MSZ", "%Y-%m-%d-%H:%M:%S.%f%Z", 0)]
INVALID_TIMESTAMP_SYMBOL_REGEX = re.compile('[`~!@#$%^&*()_={}[]|\\;\'\"<>?]')
ONLY_NUMBERS_REGEX = re.compile("[0-9]+")



class FieldType:
    """ Provides type and format information for a single field
    """

    def __init__(self,
                 values: list[tuple[Any, int]]) -> None:
        """ Initialize FieldType for a single field

        Arguments:
            - values: a frequency-dist in the format of a list of tuples, with
              the first tuple value being the field value, and the second being
              a count of its occurances.
        """
        self.raw_values = list(values)
        self.converted_values: dict[Any, int] = {}
        self.type_freq: dict[str, int] = {}
        self.format_freq: dict[str, int] = {}
        self.clean_type_values: list[str] = []
        self.final_field_type: str = 'unknown'
        self.final_field_format: str = 'unknown'
        self.timestamp_formats = TIMESTAMP_FORMATS


    def get_field_type(self) -> str:
        """ Returns type of field

        Returns:
            type: one of "unknown", "string", "number", "integer", "float",
                  "timestamp"
        """

        if self.raw_values is None:
            return 'unknown'

        self._build_type_freq()

        self.clean_type_values = [x for x in self.type_freq if x != 'unknown']

        self._get_field_type_rule()
        if self.final_field_type == 'unknown':
            self._get_field_type_probability()
        return self.final_field_type


    def get_field_format(self) -> str:
        total = sum(self.format_freq.values())
        for key in self.format_freq:
            if self.format_freq[key]/total >= 0.9:
                self.final_field_format = key
                break
        else:
            self.final_field_format = 'unknown'
        return self.final_field_format


    def _build_type_freq(self):
        """ Populates type dicts that reflect frequency of type
        """

        for i, (key, count) in enumerate(self.raw_values[:MAX_TYPE_SIZE]):

            if 'timestamp' in self.type_freq:
                if i in (100, 500, 1000):
                    self._sort_timestamp_formats()

            key_type, key_format, converted_val = self._get_comprehensive_type(key)
            try:
                self.type_freq[key_type] += int(count)
            except KeyError:
                self.type_freq[key_type] = int(count)
            try:
                self.format_freq[key_format] += int(count)
            except KeyError:
                self.format_freq[key_format] = int(count)
            try:
                self.converted_values[converted_val] += int(count)
            except KeyError:
                self.converted_values[converted_val] = int(count)


    def _sort_timestamp_formats(self) -> None:
        # update counts in self.timestamp_formats
        updated_list = []
        for scope, format_name, format, count in self.timestamp_formats:
            count = self.format_freq.get(format_name, 0)
            updated_list.append((scope, format_name, format, count))

        # sort by count
        self.timestamp_formats = sorted(updated_list,
                                        key=lambda t: t[3],
                                        reverse=True)


    def _get_comprehensive_type(self,
                                value: Any) -> tuple[str, Optional[str], Optional[Any]]:
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
            return 'unknown', None, None
        elif is_float(value):
            return 'float', None, None
        elif is_integer(value):
            return 'integer', None, None
        else:
            ts_result, ts_format, converted_val = is_timestamp_extended(value,
                                                                        self.timestamp_formats)
            if ts_result:
                return 'timestamp', ts_format, converted_val
            else:
                return 'string', None, None


    def _get_field_type_rule(self) -> None:
        """ The intent is to resolve type determinations through simplistic rules:

        There is no guarantee that this approach will determine the type,
        it's simply the first attempt.
            - It ignores any 'unknown' types
            - If it only finds values of a single type - then it will return that
            - if there only two types, and they are ints and floats then it will
              return float
        """
        float_set_2i = set(['integer', 'float'])

        type_set = set(self.clean_type_values)

        if len(self.clean_type_values) == 0:
            self.final_field_type = 'unknown'
        elif len(self.clean_type_values) == 1:
            self.final_field_type = self.clean_type_values[0]
        elif len(self.clean_type_values) == 2:
            if not type_set.symmetric_difference(float_set_2i):
                self.final_field_type = 'float'



    def _get_field_type_probability(self) -> None:
        """ Determines type of field based on the type of the majority of values.
        """
        total = sum(self.type_freq.values())
        for key in self.type_freq:
            if self.type_freq[key]/total >= 0.8:
                self.final_field_type = key



def get_type(value: Any) -> str:
    """ Accepts a single string value and returns its probable type

        Types identified (and returned) include:
        - unknown
        - string
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
    elif is_timestamp(value):
        return 'timestamp'
    else:
        return 'string'



def is_timestamp_extended(value: Union[float, str],
                          timestamp_formats=TIMESTAMP_FORMATS) \
                          -> tuple[bool, Optional[str], Optional[Any]]:
    """ Returns True if arg is a date or time or datetime and if so what format

    Args:
        value          - a string in any of about 50 formats
    Returns:
        status         - True if date/time False if not
        format_name    - name of format,  ex: YYYY-MM-DD
        value_datetime - value cast as datetime
    """
    if isinstance(value, float):
        return False, None, None
    if len(value) > DATE_MAX_LEN:
        return False, None, None
    if len(value) < 8: #DATE_MIN_LEN:
        return False, None, None
    if INVALID_TIMESTAMP_SYMBOL_REGEX.match(value):
        return False, None, None

    # Validate the number of number-groups
    number_groups = ONLY_NUMBERS_REGEX.findall(value)
    if len(number_groups) < 2: # must be at least a year and day
        return False, None, None
    if len(number_groups) > 8:  # provides enough for yyyy-mm-ddThh:mm:ss.999999+0700
        return False, None, None

    # Validate the number of digits
    number_count = len(''.join(number_groups))
    if number_count < 5: # YYYY + day of month
        return False, None, None
    # Validate the number of alphas
    # if more than len('september'); return False

    for _, format_name, date_format, _ in timestamp_formats:
        try:
            t_date = datetime.datetime.strptime(value, date_format)
        except ValueError:
            pass
        else:
            #return True, format_name, t_date
            return True, date_format, t_date
    else:
        return False, None, None



def is_timestamp(value: Union[float, str],
                 timestamp_formats=TIMESTAMP_FORMATS) -> bool:
    """ Returns True if the value is a date or time or datetime

    Args:
        value             - a string of any of about 50 formats
        timestamp_formats - defaults to global TIMESTAMP_FORMATS

    Returns:
        status   - True if date/time False if not
    """
    status, format_name, value_datetime =  is_timestamp_extended(value, timestamp_formats)
    return status



def is_string(value: Any) -> bool:
    """ Returns True if the value is a string

    Note that it is subject, subject to false-negatives if the string is all
    numeric.
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
    """
    try:                    # catch integers & floats
        float(value)
        return False
    except TypeError:       # catch None
        return False
    except ValueError:      # catch characters
        return True



def is_integer(value: Any) -> bool:
    """ Returns True if the input is an int rather than a float or character data

        0         is True
        '3'       is True
        '-3'      is True
        3         is True
        -3        is True
        0.0       is False
        4.0       is False
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
        if isinstance(value, float):
            return False
        elif isinstance(value, str):
            if '.' in value:
                return False
        return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_float(value: Any) -> bool:
    """ Returns True if the input is a float rather than int or character data

        0.0     is True
        4.0     is True
        44.55   is True
        '33.22' is True
        0       is False
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
        if isinstance(value, str):
            if '.' not in value:
                return False
        elif isinstance(value, float):
            return True
        elif isinstance(value, int):
            return False
        float(value)
    except ValueError:
        return False
    except TypeError:
        return False
    else:
        return True



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


