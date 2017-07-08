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
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
import math
from typing import Dict, List, Tuple, Any, Union, Optional
from pprint import pprint as pp

import datagristle.field_type as field_type
import datagristle.common as common


FreqType = List[Tuple[Any, int]]
StrFreqType = List[Tuple[str, int]]
NumericFreqType = List[Tuple[Union[int, float], int]]



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



def get_variance_and_stddev(values: NumericFreqType, mean: Optional[float] = None)\
                            -> Tuple[Optional[float], Optional[float]]:
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
    if not values:
        return (None, None)

    clean_values = get_clean_freq_dist_for_numbers(values)
    if mean is None:
        mean = get_mean(clean_values)

    accum = sum([math.pow(mean - x[0], 2) * x[1] for x in clean_values])
    count = sum([x[1] for x in clean_values])

    variance = accum / count
    stddev = math.sqrt(variance)
    return variance, stddev




def get_mean(values: FreqType) -> Optional[float]:
    ''' Calculates the mean value of a frequency distribution.

    The mean value takes into consideration the number of times each value
    occur - based on a frequency number.  Supported formats include either
    a dictionary or a list of tuples.  In either case non-integer|float values
    will be ignored.

    Args:
        values: list of tuples.
    Returns:
        A float that represents the mean value.  If the argument is empty
        then it will return None.
    '''
    if not values:
        return None

    clean_values = get_clean_freq_dist_for_numbers(values)

    accum = sum([float(x[0]) * x[1] for x in clean_values])
    count = sum([x[1] for x in clean_values])

    try:
        return accum / count
    except ZeroDivisionError:
        return 0.0



def get_median(values: FreqType) -> Optional[float]:
    ''' Calculates the median value of a frequency distribution.

    The median value takes into consideration the number of times each value
    occur - based on a frequency number.

    Args:
        values: list of tuples.  Non-integer|float values will be ignored.
    Returns:
        A float that represents the median value.  If the argument is empty
        then it will return None.
    '''
    if not values:
        return None

    # prep the list of tuples:
    sorted_values = sorted(get_clean_freq_dist_for_numbers(values))

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




def get_clean_freq_dist_for_numbers(values: NumericFreqType) -> NumericFreqType:
    """
    Raises: TypeError if input is None
    """
    if values is None:
        raise TypeError('invalid input is None')
    if isinstance(values, dict):
        raise NotImplementedError('dictionaries are no longer supported')
    isnumeric = common.isnumeric
    return [(cast_numeric(x[0]), x[1]) for x in values if isnumeric(x[0]) and isnumeric(x[1])]



def get_clean_freq_dist_for_text(values: StrFreqType) -> StrFreqType:

    if values is None:
        raise TypeError('invalid input is None')
    if isinstance(values, dict):
        raise NotImplementedError('dictionaries are no longer supported')
    is_unknown = field_type.is_unknown
    return [(x[0], x[1]) for x in values if isinstance(x[0], str) and not is_unknown(x[0])]



def cast_numeric(val: Union[int, float]) -> Union[int, float]:
    try:
        float_val = float(val)
    except (ValueError, TypeError):
        raise ValueError('{} is not numeric'.format(val))

    try:
        int_val = int(val)
    except ValueError:
        return float_val

    if int_val == float_val:
        return int_val
    else:
        return float_val


