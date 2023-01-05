#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldDeterminator   - class runs all checks on all fields

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
import datetime as dt
import math
from operator import itemgetter
from pprint import pprint as pp
import sys
from typing import Optional, Any, Union, Iterable

from pydantic import BaseModel, validator, ValidationError

from datagristle import common
from datagristle import csvhelper
from datagristle import field_type as typer

#------------------------------------------------------------------------------
# field_freq max dictionary size defaults:
# The sizes are based on these assumptions:
#   Single col with 10 million unique items, average item length of 20 bytes
#   plus a hashed version of item key, plus two pointers.  That's about 40
#   bytes per entry, or 400 MBytes maximum in this case.
#   Multi-column needs to be more conservative since there could be 10,20, or
#   80 different columns.  So it's limited to 1/10th the number of items.
#------------------------------------------------------------------------------
MAX_FREQ_SINGLE_COL_DEFAULT = 10_000_000 # ex: 1 col, 10 mil items with 20 byte key = ~400 MB
MAX_FREQ_MULTI_COL_DEFAULT  = 1_000_000  # ex: 10 cols, ea with 1 mil & 20 byte key = ~400 MB tot

FreqType = Iterable[tuple[Any, int]]
StrFreqType = Iterable[tuple[str, int]]
NumericFreqType = Iterable[tuple[Union[float, int], int]]


class FieldProfile(BaseModel):
    field_number: int
    field_name: str
    field_type: str
    value_known_cnt: int
    field_profiled_cnt: int
    value_counts: dict[str, int]
    value_trunc: bool
    value_unknown_cnt: int


    @validator('field_type')
    def field_type_validator(cls, val):
        if val not in ('integer', 'string', 'timestamp', 'float', 'unknown'):
            raise ValueError(f'Invalid field_type: {val}')
        return val

    def get_top_values(self,
                       limit: Optional[int]=None) -> list[tuple[Any, int]]:
        """  Returns a list of highest-occuring field values along with their frequency.
        Args:
            - limit - is an optional limit on the number of values to show
        Returns:
            - rev_sort_list, which is a list of lists.
            - For example, the following hypothetical results would be
                returned for a field that describes the number of failing
                schools by state with a limit of 3:
                [['ca',120], ['ny',89], ['tx',71]]
        """
        return sorted(list(self.value_counts.items()),
                      key=itemgetter(1),
                      reverse=True)[:limit]

    def _get_common_display_properties(self):
        display = []
        display.append(('Type', self.field_type))
        display.append(('Truncated', self.value_trunc))
        display.append(('Min', self.value_min))
        display.append(('Max', self.value_max))
        return display

    def get_display_properties(self):
        display = self._get_common_display_properties()
        for key, value in self.__dict__.items():
            if 'counts' in key:
                continue
            if key.endswith('_cnt'):
                continue
            if key in [x[0] for x in display]:
                continue
            display.append((key, str(value)))
        return display

    def get_display_counts(self):
        display = []
        display.append(('Unique Values', str(len(self.value_counts))))
        display.append(('Known Values', str(self.value_known_cnt)))
        display.append(('Unknown Values', str(self.value_unknown_cnt)))
        return display



class FloatFieldProfile(FieldProfile):
    value_min: float
    value_max: float

    value_mean: float
    value_median: float
    value_variance: float
    value_stddev: float
    value_decimals: int

    def get_display_properties(self):
        display = self._get_common_display_properties()
        display.append(('Decimals', str(self.value_decimals)))
        display.append(('Mean', float_truncator(self.value_mean)))
        display.append(('Median', float_truncator(self.value_median)))
        display.append(('Stddev', float_truncator(self.value_stddev)))
        display.append(('Variance', float_truncator(self.value_variance)))
        return display



class IntegerFieldProfile(FieldProfile):
    value_min: int
    value_max: int

    value_mean: float
    value_median: float
    value_variance: float
    value_stddev: float

    def get_display_properties(self):
        display = self._get_common_display_properties()
        display.append(('Mean', float_truncator(self.value_mean)))
        display.append(('Median', float_truncator(self.value_median)))
        display.append(('Stddev', float_truncator(self.value_stddev)))
        display.append(('Variance', float_truncator(self.value_variance)))
        return display



class StringFieldProfile(FieldProfile):
    value_min: str
    value_max: str

    value_case: str
    value_min_length: int
    value_max_length: int
    value_mean_length: float

    def get_display_properties(self):
        display = self._get_common_display_properties()
        display.append(('Case', self.value_case))
        display.append(('Min Length', self.value_min_length))
        display.append(('Max Length', self.value_max_length))
        display.append(('Mean Length', float_truncator(self.value_mean_length)))
        return display



class TimestampFieldProfile(FieldProfile):
    value_min: dt.datetime
    value_max: dt.datetime
    formatted_value_counts: dict[dt.datetime, int]

    field_format: str

    def get_display_properties(self):
        display = self._get_common_display_properties()
        display = [x for x in display if x[0] not in ('Min', 'Max')]
        display.append(('Format', self.field_format))
        display.append(('Min', dt.datetime.strftime(self.value_min, self.field_format)))
        display.append(('Max', dt.datetime.strftime(self.value_max, self.field_format)))
        return display



class FieldProfileBuilder:

    def __init__(self,
                 field_number,
                 field_name,
                 max_items: int):

        self.field_number = field_number
        self.field_name = field_name
        self.value_counts: dict[str, int] = {}
        self.formatted_value_counts: dict[Any, int] = {}
        self.value_trunc = False
        self.max_items = max_items
        self.values_profiled_cnt = 0
        self.field_type: str
        self.field_format: str = 'unknown'
        self.invalid_row_cnt = 0


    def add_value(self, value):

        if self.value_trunc:
            return

        self.values_profiled_cnt += 1
        try:
            self.value_counts[value] += 1
        except KeyError:
            self.value_counts[value] = 1

        if self.max_items > -1 and len(self.value_counts) >= self.max_items:
            print(f'    WARNING: freq dict is too large for field {self.field_number}.')
            print(f'             Profiling will be based on the first {self.values_profiled_cnt} rows')
            print(f'             and {self.max_items} number of unique entries.')
            print(f'             Use the gristle_profiler --max-freq option to increase dict size.')
            self.value_trunc = True


    def truncated(self):
        self.value_trunc = True


    def determine_type_and_format(self,
                                   field_type_override):

        field_typer = typer.FieldType(self.value_counts.items())
        self.field_type = field_typer.get_field_type()
        if self.field_type == 'timestamp':
            self.field_format = field_typer.get_field_format()

        if field_type_override:
            self.field_type = field_type_override
        if not self.field_type:
            common.abort('ERROR: self.field_type is EMPTY! aborting')


    def add_invalid_row(self):
        self.invalid_row_cnt += 1


    def build_formatted_value_counter(self):
        assert self.field_type
        assert self.field_format
        if self.field_type != 'timestamp':
            return
        if self.field_format == 'unknown':
            return
        for (timestamp_string, count) in self.value_counts.items():
            try:
                self.formatted_value_counts[dt.datetime.strptime(timestamp_string,
                                            self.field_format)] = count
            except ValueError:
                pass


    def output(self):

        common_fields = {'field_number':self.field_number,
                         'field_name':self.field_name,
                         'field_type':self.field_type,
                         'field_profiled_cnt':self.values_profiled_cnt,
                         'value_trunc':self.value_trunc}

        if self.field_type in ('integer'):
            num_values = NumericTypeFreq(self.value_counts.items(), self.field_type)
            mean = num_values.get_mean()
            (variance, stddev) = num_values.get_variance_and_stddev()
            clean_value_cnt = num_values.get_clean_value_count()
            profile = IntegerFieldProfile(**common_fields,
                                          value_known_cnt=clean_value_cnt,
                                          value_unknown_cnt=self.values_profiled_cnt - clean_value_cnt,
                                          value_min=num_values.get_min(),
                                          value_max=num_values.get_max(),
                                          value_mean=mean,
                                          value_median=num_values.get_median(),
                                          value_variance=variance,
                                          value_stddev=stddev,
                                          value_decimals=num_values.get_max_decimals(),
                                          value_counts=self.value_counts)
        elif self.field_type in ('float'):
            num_values = NumericTypeFreq(self.value_counts.items(), self.field_type)
            mean = num_values.get_mean()
            (variance, stddev) = num_values.get_variance_and_stddev()
            clean_value_cnt = num_values.get_clean_value_count()

            profile = FloatFieldProfile(**common_fields,
                                        value_known_cnt=clean_value_cnt,
                                        value_unknown_cnt=self.values_profiled_cnt - clean_value_cnt,
                                        value_min=num_values.get_min(),
                                        value_max=num_values.get_max(),
                                        value_mean=mean,
                                        value_median=num_values.get_median(),
                                        value_variance=variance,
                                        value_stddev=stddev,
                                        value_decimals=num_values.get_max_decimals(),
                                        value_counts=self.value_counts)
        elif self.field_type in ('string'):
            str_values = StrTypeFreq(list(self.value_counts.items()))
            clean_value_cnt = str_values.get_clean_value_count()
            profile = StringFieldProfile(**common_fields,
                                          value_known_cnt=clean_value_cnt,
                                          value_unknown_cnt=self.values_profiled_cnt - clean_value_cnt,
                                          value_min=str_values.get_min(),
                                          value_max=str_values.get_max(),
                                          value_case=str_values.get_case(),
                                          value_min_length=str_values.get_min_length(),
                                          value_max_length=str_values.get_max_length(),
                                          value_mean_length=str_values.get_mean_length(),
                                          value_counts=self.value_counts)
        elif self.field_type in ('timestamp'):
            ts_values = TimestampTypeFreq(self.formatted_value_counts.items(),
                                          self.field_format)
            clean_value_cnt = ts_values.get_clean_value_count()
            profile = TimestampFieldProfile(**common_fields,
                                          value_known_cnt=clean_value_cnt,
                                          value_unknown_cnt=self.values_profiled_cnt - clean_value_cnt,
                                          value_min=ts_values.get_min(),
                                          value_max=ts_values.get_max(),
                                          field_format=self.field_format,
                                          value_counts=self.value_counts,
                                          formatted_value_counts=self.formatted_value_counts)
        elif self.field_type in ('unknown'):
            ts_values = TimestampTypeFreq(self.formatted_value_counts.items(),
                                          self.field_format)
            profile = FieldProfile(**common_fields,
                                   value_known_cnt=ts_values.get_clean_value_count(),
                                   value_unknown_cnt=self.values_profiled_cnt - ts_values.get_clean_value_count(),
                                   value_min=ts_values.get_min(),
                                   value_max=ts_values.get_max(),
                                   field_format=self.field_format,
                                   value_counts=self.value_counts,
                                   formatted_value_counts=self.formatted_value_counts)
        else:
            raise ValueError(f'Invalid self.field_type: {self.field_type}')

        return profile



class RecordProfiler:
    """ Examines ALL fields within a file

    Arguments
        - read_limit: a performance setting that stops file reads after
          this number.  The default is -1 which means 'no limit'.

    """

    def __init__(self,
                 input_handler,
                 field_cnt: int,
                 dialect: csvhelper.Dialect,
                 read_limit = -1,
                 verbosity: str='normal') -> None:

        self.input_handler = input_handler
        self.field_cnt = field_cnt  # offset from 1
        self.dialect = dialect
        self.read_limit = read_limit
        self.verbosity = verbosity

        self.field_profile_builders: dict[int, Any] = {}
        self.field_profile: dict[int, Union[TimestampFieldProfile, IntegerFieldProfile, FloatFieldProfile]] = {}

        self.invalid_rec_missing_fields_cnt = 0
        self.invalid_rec_extra_fields_cnt = 0

        def set_field_defaults(val):
            return {i:val for i in range(self.field_cnt)}

        #--- public field dictionaries - organized by field_number --- #
        # every field should have a key in every one of these dictionaries
        # but if the dictionary doesn't apply, then the value may be None
        self.field_freq:        dict[int, dict[Any, int]] = {i:{} for i in range(self.field_cnt)}

        assert 0 < field_cnt < 1000


    def analyze_fields(self,
                       field_number: Optional[int] = None,
                       field_types_overrides: dict[int, str] = {},
                       max_value_counts = -1) -> None:
        """ Determines types, names, and characteristics of fields.

        Arguments:
            - field_number: if None, then analyzes all fields, otherwise
                analyzes just the single field (based on zero-offset)
            - field_types_overrides: allows user to override the autodetected types
            - max_value_counts: a performance setting that caps the maximum size
              of the 'value_counts' dictionary used to hold values found within a field.

        Returns:
            - None
        """
        assert field_number is None or field_number > -1
        assert isinstance(field_types_overrides, dict)

        if self.verbosity in ('high', 'debug'):
            print('Field Analysis Progress: ')

        #---- set max items for the value counters ----------------------
        if max_value_counts == -1:
            if field_number is None:
                max_value_counts = MAX_FREQ_MULTI_COL_DEFAULT
            else:
                max_value_counts = MAX_FREQ_SINGLE_COL_DEFAULT


        #---- build field profilers ----------------------------
        for f_no in range(self.field_cnt):
            if field_number is None or field_number == f_no:
                self.field_profile_builders[f_no] = FieldProfileBuilder(field_number=f_no,
                                                                        field_name=self.input_handler.get_field_name(f_no),
                                                                        max_items=max_value_counts)

        #---- build field_freqs --------------------------------
        self._build_field_value_counters(field_number)

        #---- build aggregate fields ---------------------------
        for f_no in range(self.field_cnt):
            if field_number is None or field_number == f_no:
                type_override = field_types_overrides.get(f_no)
                self.field_profile_builders[f_no].determine_type_and_format(type_override)
                self.field_profile_builders[f_no].build_formatted_value_counter()
                try:
                    self.field_profile[f_no] = self.field_profile_builders[f_no].output()
                except NoDataError:
                    pass


    def _build_field_value_counters(self,
                                    field_number):

        for rec in self.input_handler:

            if len(rec) > self.field_cnt:
                self.invalid_rec_extra_fields_cnt += 1
            if len(rec) < self.field_cnt:
                self.invalid_rec_missing_fields_cnt += 1

            for f_no, value in enumerate(rec):
                if field_number is None or field_number == f_no:
                    self.field_profile_builders[f_no].add_value(value)
                    if f_no >= self.field_cnt:
                        break

            # Handle read limit
            if self.read_limit > -1 and self.read_limit <= self.input_handler.rec_cnt:
                for f_no in range(self.field_cnt):
                    self.field_profile_builders[f_no].truncated()
                break



class TypeFreq:

    def __init__(self,
                 values: FreqType,
                 field_type: str = 'unknown'):

        self.values = values
        self.field_type = field_type
        self.clean_values: list[tuple] = []
        self.unknown_values: list[tuple] = []
        self.invalid_values: list[tuple] = []
        self._separate_values()


    def _separate_values(self):
        for value, count in self.values:
            if value == '' or typer.is_unknown(value):
                self.unknown_values.append((value, count))
            else:
                self.clean_values.append((value, count))



    def get_clean_value_count(self):
        return sum([x[1] for x in self.clean_values])


    def get_min(self):
        """ Returns the minimum value of the input.

        Ignores unknown values, if no values found besides unknown it will
        just return 'None'

        Outputs:
            - the single minimum value of the appropriate type
        """
        if not self.clean_values:
            return None
        else:
            self.min = str(min([x[0] for x in self.clean_values]))
            return self.min


    def get_max(self):
        """ Returns the maximum value of the input.

        Ignores unknown values, if no values found besides unknown it will
        just return 'None'

        Outputs:
            - the single maximum value of the appropriate type
        """
        if not self.clean_values:
            return None
        else:
            self.max = str(max([x[0] for x in self.clean_values]))
            return self.max


    def get_formatted_min(self):
        return self.min


    def get_formatted_max(self):
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
        self.mean_length: float


    def get_case(self):
        """" Returns a string name for the case of a string type field.

        Returns:
           - case: one of: 'mixed', 'lower', 'upper' 'unknown'
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
        """ Returns the maximum length value of the input.

        If no values found besides unknown it will just return 'None'

        Outputs:
            - the single maximum value
        """
        max_length = 0
        return max([len(value[0]) for value in self.clean_values]) or max_length


    def get_min_length(self) -> int:
        """ Returns the minimum length value of the input.

        If no values found besides unknown it will just return 999999

        Outputs:
            - the single minimum value
        """
        min_length = 999999
        return min([len(value[0]) for value in self.clean_values]) or min_length


    def get_mean_length(self) -> float:
        """ Returns the mean length value of the input.

        If no values found besides unknown it will return 0.

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
                 values: StrFreqType,
                 timestamp_format: str):

        super().__init__(values)

        self.min: dt.datetime
        self.max: dt.datetime
        self.timestamp_format = timestamp_format


    def get_min(self):
        """ Returns the minimum value of the input.

        Ignores unknown values, if no values found besides unknown it will
        just return 'None'

        Outputs:
            - the single minimum value of the appropriate type
        """
        if not self.clean_values:
            return None
        else:
            min_val = min([x[0] for x in self.clean_values])
            if min_val:
                self.min = min_val
            else:
                self.min = None
            return self.min


    def get_max(self):
        """ Returns the minimum value of the input.

        Ignores unknown values, if no values found besides unknown it will
        just return 'None'

        Outputs:
            - the single minimum value of the appropriate type
        """
        if not self.clean_values:
            return None
        else:
            max_val = max([x[0] for x in self.clean_values])
            if max_val:
                self.max = max_val
            else:
                self.max = None
            return self.max


class NumericTypeFreq(TypeFreq):

    def __init__(self,
                 values: NumericFreqType,
                 field_type: str):

        super().__init__(values, field_type)

        assert field_type in ('integer', 'float')
        self.min: Union[float, int]
        self.max: Union[float, int]
        self.mean: float
        self.median: Optional[float]
        self.variance: float
        self.stddev: float


    def _separate_values(self):
        """
        Raises: TypeError if input is None
        """
        values = self.values
        if values is None:
            raise TypeError('invalid input is None')
        isnumeric = common.isnumeric
        cleaned = []
        cleaned = self.clean_values
        for value in values:
            if not isnumeric(value[0]):
                self.invalid_values.append(value)
            if not isnumeric(value[1]):
                self.invalid_values.append(value)
            try:
                cleaned.append((self.cast_numeric(value[0], self.field_type), value[1]))
            except ValueError:
                continue


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


    def get_variance_and_stddev(self) -> tuple[float, float]:
        ''' Calculates the variance & population stddev of a frequency distribution.

        The calculation takes into consideration the number of times each value
        occurs - based on a frequency number.

        Returns:
            A pair of floats that represents the variance and standard deviation.
            If the argument is empty then it will return None, None.
        '''
        if not self.clean_values:
            #return (None, None)
            return (0.0, 0.0)

        assert self.mean is not None

        accum = sum([math.pow(self.mean - x[0], 2) * x[1] for x in self.clean_values])
        count = sum([x[1] for x in self.clean_values])

        self.variance = accum / count
        self.stddev = math.sqrt(self.variance)
        return self.variance, self.stddev


    def get_max_decimals(self) -> Optional[int]:
        ''' Returns the maximum number of decimal places on any value.

        Not using typical numeric methods since they can easily expand the size
        of the decimals due to floating point characteristics.
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
        """ Return the value cast as the field type (int or float)

        Raises
            ValueError if it cannot cast the value.
        """

        if field_type == 'float':
            try:
                float_val = float(val)
            except (ValueError, TypeError):
                raise ValueError('{} is not numeric'.format(val))
            else:
                return float_val

        try:
            int_val = int(val)
        except ValueError:  # it may be a value like: "9.9"
            raise ValueError('{} is not numeric'.format(val))
        else:
            return int_val


def float_truncator(numeric_value, max_decimals=3):
    """ trim unnecessary digits

    Note though that quoted integers may be recorded with a single digit of precision,
    and max_decimals of 1.   So, when this is run on an unquoted file it will produce
    two decimals, but on a quoted file three.
    """
    str_value = str(numeric_value)
    assert str_value.count('.') <= 1
    return f'{numeric_value:.{max_decimals+2}f}'




class NoDataError(ValueError):
    """Error due to empty results
    """
    pass

class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass
