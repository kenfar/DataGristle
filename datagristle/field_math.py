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
from typing import Dict, List, Tuple, Any, Union
from pprint import pprint as pp

import datagristle.field_type as field_type
import datagristle.common as common




def get_mean_length(values: Dict[str, int]) -> int:
    ''' Calculates the mean length of strings in a frequency distribution.

    The mean length takes into consideration the number of times each value
    occurs - based on a frequency number.  Supported formats include either
    a dictionary or a list of tuples.  In either case non-string values
    will be ignored.

    Args:
        values: either a dictionary or list of tuples.  If a dictionary, then
            the keys must be strings and the values (occurrences of the key)
            must be integers.
    Returns:
        A float that represents the mean value.  If the argument is empty
        then it will return None.
    '''

    if not values:
        return None

    clean_values = get_clean_freq_dist_for_text(values)

    accum = sum([len(x[0]) * x[1] for x in clean_values])
    count = sum([x[1] for x in clean_values])

    try:
        return accum / count
    except ZeroDivisionError:
        return 0



def get_variance_and_stddev(values, mean=None):
    ''' Calculates the variance & population stddev of a frequency distribution.

    The calculation takes into consideration the number of times each value
    occurs - based on a frequency number.  Supported formats include either
    a dictionary or a list of tuples.  In either case non-integer|float values
    will be ignored.

    Args:
        values: either a dictionary or list of tuples.  If a dictionary, then
            the keys must be either a float or int and the values (occurrences
            of the key) must be integers.
    Returns:
        A pair of floats that represents the variance and standard deviation.
        If the argument is empty then it will return None.
    '''
    if not values:
        return (None, None)

    clean_values = get_clean_freq_dist_for_numbers(values)
    if mean is None:
        mean = get_mean(values)

    accum = sum([math.pow(mean - x[0], 2) * x[1] for x in clean_values])
    count = sum([x[1] for x in clean_values])

    try:
        variance = accum / count
        stddev   = math.sqrt(variance)
        return variance, stddev
    except ZeroDivisionError:
        return None, None




def get_mean(values: Union[List[Tuple[Any, int]], Dict[Any, int]]) -> float:
    ''' Calculates the mean value of a frequency distribution.

    The mean value takes into consideration the number of times each value
    occur - based on a frequency number.  Supported formats include either
    a dictionary or a list of tuples.  In either case non-integer|float values
    will be ignored.

    Args:
        values: either a dictionary or list of tuples.  If a dictionary, then
            the keys must be either a float or int and the values (occurrences
            of the key) must be integers.
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
        return 0



def get_median(values: Union[List[Tuple[Any, int]], Dict[Any, int]]) -> float:
    ''' Calculates the median value of a frequency distribution.

    The median value takes into consideration the number of times each value
    occur - based on a frequency number.  Supported formats include either
    a dictionary or a list of tuples.  In either case non-integer|float values
    will be ignored.

    Args:
        values: either a dictionary or list of tuples.  If a dictionary, then
            the keys must be either a float or int and the values (occurrences
            of the key) must be integers.
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
        center_top    = center + 1
        center_bottom = center
    else:
        center_top    = math.ceil(center)
        center_bottom = math.ceil(center)

    # get the values in the center positions:
    accum = 0
    center_top_value = None
    center_bottom_value = None
    for entry in sorted_values:
        accum += entry[1]
        if accum >= center_bottom and center_bottom_value is None:
            center_bottom_value = entry[0]
        if accum >= center_top and center_top_value is None:
            center_top_value = entry[0]
            break
    else:
        return None

    return (center_bottom_value + center_top_value) / 2

    # alternate ending: if we want result type to match argument type
    #if type_int:
    #   result = round((center_bottom_value + center_top_value) / 2)
    #else:
    #   result = (center_bottom_value + center_top_value) / 2
    #return result



def get_clean_freq_dist_for_numbers(values):
    if isinstance(values, dict):
        values = list(values.items())
    isnumeric = common.isnumeric
    clean_values = [(number(x[0]), x[1]) for x in values if isnumeric(x[0])]
    return clean_values



def get_clean_freq_dist_for_text(values):
    if isinstance(values, dict):
        values = list(values.items())
    is_unknown = field_type.is_unknown
    clean_values = [(x[0], x[1]) for x in values if not is_unknown(x[0])]
    return clean_values



def number(val) -> Union[int, float]:
    if is_int(val):
        return int(val)
    elif is_float(val):
        return float(val)
    else:
        raise ValueError('%s is not numeric' % val)



def is_float(val) -> bool:
    try:
        _ = float(val)
    except ValueError:
        return False
    else:
        return True



def is_int(val) -> bool:
    try:
        float_val = float(val)
        int_val = int(float_val)
    except ValueError:
        return False
    else:
        return float_val == int_val
