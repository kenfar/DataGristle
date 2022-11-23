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
    Copyright 2011-2022 Ken Farmer
"""
import csv
from typing import List, Union, Dict, Tuple, Any, Optional
from pprint import pprint as pp

import datagristle.field_type as typer
import datagristle.csvhelper as csvhelper
import datagristle.common as common

MAX_FREQ_SIZE_DEFAULT = 1000000     # limits entries within freq dictionaries

StrFreqType = List[Tuple[str, int]]



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



class StrFieldFreqMetrics:

    def __init__(self,
                 values: StrFreqType):

        self.values = values
        self.clean_values = self._value_cleaner(self.values)

        self.case: str
        self.min: str
        self.max: str
        self.min_length: int
        self.max_length: int
        self.mean_length: int



    def _value_cleaner(self,
                       values: StrFreqType):

        return [x for x in self.values
               if x != ''
               and not typer.is_unknown(x[0])]


    def get_case(self):
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

        lower_cnt = sum([x[1] for x in self.clean_values if x[0].islower()])
        upper_cnt = sum([x[1] for x in self.clean_values if x[0].isupper()])
        mixed_cnt = len(self.clean_values) - lower_cnt - upper_cnt

        # evaluate mix of types:
        if mixed_cnt:
            case = 'mixed'
        elif lower_cnt:
            case = 'lower'
        elif upper_cnt:
            case = 'upper'
        else:
            case = 'unknown'

        return case


    def get_max_length(self) -> int:
        """ Returns the maximum length value of the input.   If
            no values found besides unknown it will just return 'None'

            Inputs:
            - dictionary or list of string values
            Outputs:
            - the single maximum value
        """
        max_length = 0
        return max([len(value[0]) for value in self.clean_values]) or max_length


    def get_min_length(self) -> int:
        """ Returns the minimum length value of the input.   If
            no values found besides unknown it will just return 999999

        Inputs:
        - dictionary or list of string values
        Outputs:
        - the single minimum value
        """
        min_length = 999999
        return min([len(value[0]) for value in self.clean_values]) or min_length


    def get_mean_length(self) -> int:
        """ Returns the mean length value of the input.   If
            no values found besides unknown it will just return None

        Inputs:
        - dictionary or list of string values
        Outputs:
        - the single minimum value
        """

        accum = sum([len(x[0]) * x[1] for x in self.clean_values])
        count = sum([x[1] for x in self.clean_values])

        try:
            self.mean_length = accum / count
        except ZeroDivisionError:
            self.mean_length = 0
        return self.mean_length


    def get_min(self):
        """ Returns the minimum value of the input.  Ignores unknown values, if
            no values found besides unknown it will just return 'None'

            Inputs:
            - value_type - one of integer, float, string, timestamp
            - dictionary or list of string values
            Outputs:
            - the single minimum value of the appropriate type
        """
        self.min = min([x[0] for x in self.clean_values])
        return self.min


    def get_max(self):
        """ Returns the maximum value of the input.  Ignores unknown values, if
            no values found besides unknown it will just return 'None'

            Inputs:
            - value_type - one of integer, float, string, timestap
            - dictionary or list of string values
            Outputs:
            - the single maximum value of the appropriate type
        """
        self.max = max([x[0] for x in self.clean_values])
        return self.max



class TimestampFieldFreqMetrics:

    def __init__(self,
                 values: StrFreqType):

        self.values = values
        self.clean_values = self._value_cleaner(self.values)

        self.min: str
        self.max: str


    def _value_cleaner(self,
                       values: StrFreqType):

        return [x for x in self.values
               if x != ''
               and not typer.is_unknown(x[0])]


    def get_min(self):
        """ Returns the minimum value of the input.  Ignores unknown values, if
            no values found besides unknown it will just return 'None'

            Inputs:
            - value_type - one of integer, float, string, timestamp
            - dictionary or list of string values
            Outputs:
            - the single minimum value of the appropriate type
        """
        self.min = min([x[0] for x in self.clean_values])
        return self.min


    def get_max(self):
        """ Returns the maximum value of the input.  Ignores unknown values, if
            no values found besides unknown it will just return 'None'

            Inputs:
            - value_type - one of integer, float, string, timestap
            - dictionary or list of string values
            Outputs:
            - the single maximum value of the appropriate type
        """
        self.max = max([x[0] for x in self.clean_values])
        return self.max

