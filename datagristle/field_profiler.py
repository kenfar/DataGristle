#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldDeterminator   - class runs all checks on all fields
    Todo:
      - change get_types to consider whatever has 2 STDs
      - replace get_types freq length logic with something that says,
        if all types are basically numeric, choose float
      - add quartiles, variances and standard deviations
      - add statistical analysis for data quality
      - add histogram to automatically bucketize data
      - consistency metric
      - leverage list comprehensions more
      - consider try/except in get_min() & get_max() int/float conversion
      - change returned data format to be based on field

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
import csv
import math
from operator import itemgetter
from pprint import pprint as pp
from typing import Optional, List, Tuple, Dict, Any, Union

from datagristle import common
from datagristle import csvhelper
import datagristle.field_type as typer

#------------------------------------------------------------------------------
# field_freq max dictionary size defaults:
# The sizes are based on these assumptions:
#   Single col with 10 million unique items, average item length of 20 bytes
#   plus a hashed version of item key, plus two pointers.  That's about 40
#   bytes per entry, or 400 MBytes maximum in this case.
#   Multi-column needs to be more conservative since there could be 10,20, or
#   80 different columns.  So it's limited to 1/10th the number of items.
#------------------------------------------------------------------------------
MAX_FREQ_SINGLE_COL_DEFAULT = 10000000 # ex: 1 col, 10 mil items with 20 byte key = ~400 MB
MAX_FREQ_MULTI_COL_DEFAULT  = 1000000  # ex: 10 cols, each with 1 mil entries & 20 byte key = ~400 MB total
FreqType = List[Tuple[Any, int]]
StrFreqType = List[Tuple[str, int]]
NumericFreqType = List[Tuple[Union[int, float], int]]



class FieldDeterminator(object):
    """ Examines ALL fields within a file
        Output structures:
          - self.field_names  - dictionary with fieldnumber key
          - self.field_types  - dictionary with fieldnumber key
          - self.field_min    - dictionary with fieldnumber key
          - self.field_max    - dictionary with fieldnumber key
          - self.field_mean   - dictionary with fieldnumber key
          - self.field_median - dictionary with fieldnumber key
          - self.field_case   - dictionary with fieldnumber key
          - self.field_min_length   - dictionary with fieldnumber key
          - self.field_max_length   - dictionary with fieldnumber key
          - self.field_trunc  - dictionary with fieldnumber key
          - self.field_decimals - dictionary with fieldnumber key
    """

    def __init__(self,
                 input_handler,
                 field_cnt: int,
                 dialect: csvhelper.Dialect,
                 verbosity: str='normal') -> None:

        self.input_handler = input_handler
        self.field_cnt = field_cnt
        self.dialect = dialect
        self.verbosity = verbosity
        self.max_freq_number:   Optional[int] = None  # will be set in analyze_fields
        self.max_items = 999999

        def set_field_defaults(val):
            return {i:val for i in range(self.field_cnt)}

        #--- public field dictionaries - organized by field_number --- #
        # every field should have a key in every one of these dictionaries
        # but if the dictionary doesn't apply, then the value may be None
        self.field_freq:        Dict[int, Dict[Any, int]] = {i:{} for i in range(self.field_cnt)}
        self.field_names:       Dict[int, str] = {}
        self.field_types:       Dict[int, str] = {}
        self.field_trunc:       Dict[int, bool] = set_field_defaults(False)
        self.field_rows_invalid: Dict[int, int] = set_field_defaults(0)
        self.field_min:         Dict[int, Optional[Any]] = set_field_defaults(None)
        self.field_max:         Dict[int, Optional[Any]] = set_field_defaults(None)

        # Numeric Type Dicts:
        self.field_mean:        Dict[int, Optional[float]] = set_field_defaults(None)
        self.field_median:      Dict[int, Optional[float]] = set_field_defaults(None)
        self.variance:          Dict[int, Optional[float]] = set_field_defaults(None)
        self.stddev:            Dict[int, Optional[float]] = set_field_defaults(None)
        self.field_decimals:    Dict[int, Optional[int]] = set_field_defaults(None)

        # String Type Dicts:
        self.field_case:        Dict[int, Optional[str]] = set_field_defaults(None)
        self.field_max_length:  Dict[int, Optional[int]] = set_field_defaults(None)
        self.field_min_length:  Dict[int, Optional[int]] = set_field_defaults(None)
        self.field_mean_length: Dict[int, Optional[float]] = set_field_defaults(None)

        # Timestamp Type Dicts:
        self.field_format:      Dict[int, Optional[str]] = set_field_defaults(None)

        assert 0 < field_cnt < 1000


    def analyze_fields(self,
                       field_number: Optional[int] = None,
                       field_types_overrides: Optional[Dict[int, str]] = None,
                       max_freq_number: Optional[int] = None,
                       read_limit: int = -1) -> None:
        """ Determines types, names, and characteristics of fields.

            Arguments:
               - field_number: if None, then analyzes all fields, otherwise
                 analyzes just the single field (based on zero-offset)
               - field_types_overrides:
               - max_freq_number: limits size of collected frequency
                 distribution, allowing for faster analysis or analysis of very
                 large high-cardinality fields.
               - read_limit: a performance setting that stops file reads after
                 this number.  The default is -1 which means 'no limit'.
            Returns:
               - Nothing directly - populates instance variables.
        """
        assert field_number is None or field_number > -1
        self.max_freq_number = max_freq_number

        if self.verbosity in ('high', 'debug'):
            print('Field Analysis Progress: ')

        #---- set max items for the freq -----------------
        if max_freq_number is None:
            if field_number is None:
                self.max_items = MAX_FREQ_MULTI_COL_DEFAULT
            else:
                self.max_items = MAX_FREQ_SINGLE_COL_DEFAULT
        else:
            self.max_items = max_freq_number

        #---- build field_freqs --------------------------------
        for rec in self.input_handler:
            pp(rec)
            print(rec)
            self._get_field_freqs(rec)
            if read_limit > -1 and self.input_handler.rec_cnt >= read_limit:
                for f_no in range(self.field_cnt):
                    self.field_trunc[f_no] = True
                break

        #---- build aggregate fields ---------------------------
        self._get_field_types(field_types_overrides)
        self._get_field_names()

        for f_no in self.field_freq.keys():
            if self.field_types[f_no] == 'string':
                str_values = StrTypeFreq(self.field_freq[f_no].items())
                self.field_case[f_no] = str_values.get_case()
                self.field_min_length[f_no] = str_values.get_min_length()
                self.field_max_length[f_no] = str_values.get_max_length()
                self.field_mean_length[f_no] = str_values.get_mean_length()
                self.field_min[f_no] = str_values.get_min()
                self.field_max[f_no] = str_values.get_max()

            elif self.field_types[f_no] in ('integer', 'float'):
                num_values = NumericTypeFreq(self.field_freq[f_no].items(),
                                                               self.field_types[f_no])
                self.field_mean[f_no] = num_values.get_mean()
                self.field_median[f_no] = num_values.get_median()
                (self.variance[f_no], self.stddev[f_no]) = num_values.get_variance_and_stddev()
                self.field_decimals[f_no] = num_values.get_max_decimals()
                self.field_min[f_no] = num_values.get_min()
                self.field_max[f_no] = num_values.get_max()

            elif self.field_types[f_no] == 'timestamp':
                ts_values = TimestampTypeFreq(self.field_freq[f_no].items())
                self.field_min[f_no] = ts_values.get_min()
                self.field_max[f_no] = ts_values.get_max()



    def _get_field_freqs(self,
                         rec):

        field_freq = self.field_freq
        field_trunc = self.field_trunc
        max_items = self.max_items

        for field_number, key in enumerate(rec):

            try:
                if field_trunc[field_number]:
                    continue
            except KeyError:
                pass

            try:
                field_freq[field_number][key] += 1
            except KeyError:
                field_freq[field_number][key] = 1
            except IndexError:
                self.field_rows_invalid[field_number] += 1
            except AttributeError as e: # quote_nonnumeric returns floats(!)
                if ("'float' object has no attribute 'strip'")  in repr(e):
                    if field_number not in self.field_freq:
                        field_freq[field_number] = {}
                    if rec[field_number] in self.field_freq[field_number]:
                        field_freq[field_number][rec[field_number]] += 1
                    else:
                        field_freq[field_number][rec[field_number]] = 1

            if max_items > -1 and len(field_freq[field_number]) >= max_items:
                print(f'    WARNING: freq dict is too large for field {field_number} - will stop adding to it')
                field_trunc[field_number] = True


    def _get_field_types(self,
                         field_types_overrides):

        for f_no in self.field_freq.keys():
            field_typer = typer.FieldType(self.field_freq[f_no].items())
            self.field_types[f_no] = field_typer.get_field_type()

            if field_types_overrides:
                for col_no in field_types_overrides:
                    self.field_types[col_no] = field_types_overrides[col_no]
        if not self.field_types:
            common.abort('ERROR: self.field_types is EMPTY! aborting')


    def _get_field_names(self):
        self.field_names = self.input_handler.field_names


    
    def get_known_values(self, fieldno: int) -> common.FreqType:
        """ returns a frequency-distribution dictionary that is the
            self.field_freqs with unknown values removed.
        """
        return [val for val in self.field_freq[fieldno]
                if typer.is_unknown(val) is False]


    def get_top_freq_values(self,
                            fieldno: int,
                            limit: Optional[int]=None) -> List[Tuple[Any, int]]:
        """  Returns a list of highest-occuring field values along with their
             frequency.
             Args:
                 - fieldno - is the number of the field, offset from zero
                 - limit - is an optional limit on the number of values to show
             Returns:
                 - rev_sort_list, which is a list of lists.
                   - The inner list is the [field value, frequency]
                   - The outer list contains up to limit number of inner lists,
                     sorted by innerlist, frequency, descending.
                   - For example, the following hypothetical results would be
                     returned for a field that describes the number of failing
                     schools by state with
                     a limit of 3:
                        [['ca',120],
                         ['ny',89],
                         ['tx',71]]
        """
        sorted_values = sorted(list(self.field_freq[fieldno].items()), key=itemgetter(1),
                               reverse=True)
        if limit:
            return sorted_values[:limit]
        else:
            return sorted_values



class TypeFreq:

    def __init__(self,
                 values: StrFreqType,
                 field_type: str = 'unknown'):

        self.values = values
        self.field_type = field_type
        self.clean_values: List[Tuple] = self._value_cleaner(self.values)


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
        self.min = str(min([x[0] for x in self.clean_values]))
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
        self.max = str(max([x[0] for x in self.clean_values]))
        return self.max




class StrTypeFreq(TypeFreq):

    def __init__(self,
                 values: StrFreqType):

        super().__init__(values)

        self.case: str
        self.min: str
        self.max: str
        self.min_length: int
        self.max_length: int
        self.mean_length: int



    def get_case(self):
        """
        Misc notes:
            - "unknown values" are ignored
        To do:
            - consider adding consideration of proportions
            - consider capping the number of rows to check
        """
        all_lower_cnt = sum([x[1] for x in self.clean_values if x[0].islower()])
        all_upper_cnt = sum([x[1] for x in self.clean_values if x[0].isupper()])
        mixed_cnt = sum([x[1] for x in self.clean_values
			if x[0] != x[0].upper() and x[0] != x[0].lower()])

        if mixed_cnt:
            return 'mixed'
        elif all_lower_cnt and all_upper_cnt:
            return 'mixed'
        elif all_lower_cnt:
            return 'lower'
        elif all_upper_cnt:
            return 'upper'
        else:
            return 'unknown'



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



class TimestampTypeFreq(TypeFreq):

    def __init__(self,
                 values: StrFreqType):

        super().__init__(values)

        self.min: str
        self.max: str



class NumericTypeFreq(TypeFreq):

    def __init__(self,
                 values: NumericFreqType,
                 field_type: str):

        super().__init__(values, field_type)

        assert field_type in ('integer', 'float')
        self.min: Union[float, int]
        self.max: Union[float, int]
        self.mean: float
        self.median: float
        self.variance: float
        self.stddev: float


    def _value_cleaner(self,
                       values: NumericFreqType) -> NumericFreqType:
        """
        Raises: TypeError if input is None
        """
        if values is None:
            raise TypeError('invalid input is None')
        isnumeric = common.isnumeric
        def cast_to_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return [(self.cast_numeric(x[0], self.field_type), x[1])
                for x in values if isnumeric(x[0]) and isnumeric(x[1]) ]


    def get_mean(self):
        self.accum = sum([x[0] * x[1] for x in self.clean_values])
        self.count = sum([x[1] for x in self.clean_values])
        try:
            self.mean = self.accum / self.count
        except ZeroDivisionError:
            self.mean = 0.0
        return self.mean


    def get_median(self) -> Optional[float]:
        ''' Calculates the median value of a frequency distribution.

        The median value takes into consideration the number of times each value
        occur - based on a frequency number.

        Returns:
            A float that represents the median value.  If the argument is empty
            then it will return None.
        '''
        if not self.clean_values:
            self.median = None
            return self.median

        # prep the list of tuples:
        sorted_values = sorted(self.clean_values)

        # get the count and center positions:
        count = sum([x[1] for x in sorted_values])
        center = count / 2
        if count % 2 == 0:
            center_top = center + 1
            center_bottom = center
        else:
            center_top = math.ceil(center)
            center_bottom = math.ceil(center)

        # get the values in the center positions:
        accum = 0
        center_bottom_value_found = False

        for entry in sorted_values:
            accum += entry[1]
            if accum >= center_bottom and not center_bottom_value_found:
                center_bottom_value = entry[0]
                center_bottom_value_found = True
            if accum >= center_top:
                center_top_value = entry[0]
                break
        else:
            return None

        return (center_bottom_value + center_top_value) / 2


    def get_variance_and_stddev(self) -> Tuple[Optional[float],
                                               Optional[float]]:
        ''' Calculates the variance & population stddev of a frequency distribution.

        The calculation takes into consideration the number of times each value
        occurs - based on a frequency number.

        Args:
            values: a list of tuples.  Non-integer|float values will be ignored.
            mean: if the mean has already been computed it can be provided and used
            to save time.
        Returns:
            A pair of floats that represents the variance and standard deviation.
            If the argument is empty then it will return None, None.
        '''
        if not self.clean_values:
            return (None, None)

        assert self.mean

        accum = sum([math.pow(self.mean - x[0], 2) * x[1] for x in self.clean_values])
        count = sum([x[1] for x in self.clean_values])

        self.variance = accum / count
        self.stddev = math.sqrt(self.variance)
        return self.variance, self.stddev


    def get_max_decimals(self) -> Optional[int]:
        ''' Returns the maximum number of decimal places on any value.

            Not using typical numeric methods since they can easily expand the size of the decimals
            due to floating point characteristics.
        '''
        if not self.clean_values:
            self.max_decimals = None
            return self.max_decimals
        if self.field_type == 'integer':
            self.max_decimals = 0
            return self.max_decimals

        float_values = [str(x[0]) for x in self.values
                        if common.isnumeric(x[0]) and '.' in str(x[0])]

        decimals = [len(x.rsplit('.', 1)[1]) for x in float_values]

        self.max_decimals = max(decimals) if decimals else 0
        return self.max_decimals


    def cast_numeric(self,
                     val: Union[int, float],
                     field_type: str) -> Union[int, float]:
        if field_type == 'float':
            try:
                float_val = float(val)
            except (ValueError, TypeError):
                raise ValueError('{} is not numeric'.format(val))
            else:
                return float_val
        elif field_type == 'integer':
            try:
                int_val = int(val)
            except ValueError:
                raise ValueError('{} is not numeric'.format(val))
            else:
                return int_val



class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass
