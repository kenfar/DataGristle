#!/usr/bin/env python
""" Purpose of this module is to identify the mathematical characteristics of
    data.  All functions are intended to work on string data, but most are
    limited to data that can be represented as integers or floats.

    Classes & Functions Include:
      get_mean_length
      get_variance_and_stddev
      get_mean
      get_median

    Todo:
      - add quartiles, variances and standard deviations
      - add statistical analysis for data quality
      - add histogram to automatically bucketize data
      - consistency metric

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017,2022 Ken Farmer
"""
import math
from typing import Dict, List, Tuple, Any, Union, Optional
from pprint import pprint as pp

from datagristle import field_type
from datagristle import common


FreqType = List[Tuple[Any, int]]
StrFreqType = List[Tuple[str, int]]
NumericFreqType = List[Tuple[Union[int, float], int]]


class NumericFieldFreqMetrics:

    def __init__(self,
                 values: NumericFreqType,
                 field_type: str):

        assert field_type in ('integer', 'float')

        self.values = values
        self.field_type = field_type
        self.clean_values = self._clean_freq(self.values)

        self.min: Union[float, int]
        self.max: Union[float, int]
        self.mean: float
        self.median: float
        self.variance: float
        self.stddev: float


    def _clean_freq(self,
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


    def get_min(self):
        self.min = min([x[0] for x in self.clean_values])
        return self.min


    def get_max(self):
        self.max = max([x[0] for x in self.clean_values])
        return self.max




def get_mean_length(values: StrFreqType) -> float:
    ''' Calculates the mean length of strings in a frequency distribution.

    The mean length takes into consideration the number of times each value
    occurs - based on a frequency number.

    Args:
        values: a list of tuples.  Non-string values will be ignored.
    Returns:
        A float that represents the mean value.  If the argument is empty
        or null it returns 0.0.
    '''
    if not values:
        return 0.0

    clean_values = get_clean_freq_dist_for_text(values)
    accum = sum([len(x[0]) * x[1] for x in clean_values])
    count = sum([x[1] for x in clean_values])
    try:
        return accum / count
    except ZeroDivisionError:
        return 0.0



def get_clean_freq_dist_for_text(values: StrFreqType) -> StrFreqType:

    if values is None:
        raise TypeError('invalid input is None')
    is_unknown = field_type.is_unknown
    return [(x[0], x[1]) for x in values if isinstance(x[0], str) and not is_unknown(x[0])]


