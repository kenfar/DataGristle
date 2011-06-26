#!/usr/bin/env python
""" Purpose of this module is to identify the mathematical characteristics of 
    data.  All functions are intended to work on string data, but most are 
    limited to data that can be represented as integers or floats.

    Classes & Functions Include:
      get_mean()
      get_median()

    Todo:
      - fix functions to handle dictionaries of frequencies!!
      - add quartiles, variances and standard deviations
      - add statistical analysis for data quality
      - add histogram to automatically bucketize data
      - consistency metric
      - leverage list comprehensions more
      - consider try/except in get_min() & get_max() int/float conversion
      - change returned data format to be based on field
"""
from __future__ import division
import time
import datetime
import collections
import csv
import fileinput
import math

import field_type

#--- CONSTANTS -----------------------------------------------------------

MAX_FREQ_SIZE          = 10000         # limits entries within freq dictionaries


def get_median(values):
    """ Returns the median value for the input.  Ignores unknown values, 
        if no values found besides unknown it will just return 'None'

        Inputs:
          - a list or dictionary of strings
        Outputs:
          - a single value - the mean of the inputs
        Test Coverage:
          - complete via test harness
        To Do:
          - fails on dictiomaries!
    """
    clean_list = []
    for val in values:
        if field_type.is_unknown(val):
            continue
        try:
            clean_list.append(float(val))
        except TypeError:
            continue
        except ValueError:    # catches non-numbers
            continue

    if not clean_list:
        return None
    else:
        sorted_list = sorted(clean_list)

    list_len = len(sorted_list)
    if list_len % 2 == 1:
        sub = (list_len+1)//2 - 1 
        return sorted_list[sub]
    else:
        lowval  = sorted_list[list_len//2-1]
        highval = sorted_list[list_len//2]
        return (lowval + highval) / 2
           


def get_mean(values):
    """ Returns the mean (average) of the input.  Ignores unknown values, if no 
        values found besides unknown it will just return 'None'

        Inputs:
          - a list or dictionary of strings
        Outputs:
          - a single value - the mean of the inputs
        Test Coverage:
          - complete via test harness
    """
    count   = 0
    accum   = 0

    for value in values:
        try:
           accum += int(value) * int(values[value])
           count += int(values[value])
        except TypeError:       # catches list of numeric strings
           count += 1
           accum += int(value)
        except IndexError:      # catches list of integers
           count += 1
           accum += int(value)
        except ValueError:      # catches dictionary with string
           pass                 # usually 'unknown values', sometimes garbage
          
    try:
        return accum / count
    except ZeroDivisionError:
        return None



