#!/usr/bin/env python
""" Purpose of this module is to identify the mathematical characteristics of
    data.  All functions are intended to work on string data, but most are
    limited to data that can be represented as integers or floats.

    Classes & Functions Include:
      get_mean_length
      get_variance_and_stddev
      get_mean
      GetDictMedian

    Todo:
      - fix functions to handle dictionaries of frequencies!!
      - add quartiles, variances and standard deviations
      - add statistical analysis for data quality
      - add histogram to automatically bucketize data
      - consistency metric
      - leverage list comprehensions more
      - change returned data format to be based on field

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""
from __future__ import division
import gristle.field_type as field_type
import math


#--- CONSTANTS -----------------------------------------------------------

MAX_FREQ_SIZE          = 10000         # limits entries within freq dictionaries



def get_mean_length(values):
    """ Returns the mean (average) length of the input.  Ignores unknown 
        values, if no values found besides unknown it will just return 'None'

        Inputs:
          - a dictionary of frequency distribution - with all data of a 
            string type, and character keyss and numeric data representing
            occurances of the keys.  Exceptions will be ignored.
        Outputs:
          - a single value - the mean of the inputs
        Test Coverage:
          - complete via test harness
    """
    accum   = 0
    count   = 0
    for value in values:
        if not field_type.is_unknown(value):
            try:
                accum += len(value) * int(values[value])
                count += int(values[value])
            except ValueError:
                pass                # usually 'unknown values', sometimes garbage
    try:
        return accum / count
    except ZeroDivisionError:
        return None


def get_variance_and_stddev(values, mean=None):
    """ Returns the variance & standard deviation of the input.  
        Ignores unknown and character values, if no values found besides 
        unknown it will just return 'None'.  Note this the equation 
        implemented involves division by the number of entries, not division
        by the number of entries + 1.

        Inputs:
          - a dictionary of frequency distribution - with all data of a 
            string type, but numeric keys and numeric data representing
            occurances of the keys.  Exceptions will be ignored.
        Outputs:
          - a single value - the mean of the inputs
        Test Coverage:
          - complete via test harness
    """
    count   = 0
    accum   = 0

    if values and not mean:
        mean = get_mean(values)

    for value in values:
        try:
            accum += math.pow(mean - int(value), 2)  * int(values[value])
            count += int(values[value])
        except ValueError:      # catches dictionary with string
            pass                # usually 'unknown values', sometimes garbage

    try:
        variance = accum / count
        stddev   = math.sqrt(variance)
        return variance, stddev
    except ZeroDivisionError:
        return None, None



def get_mean(values):
    """ Returns the mean (average) of the input.  Ignores unknown values, if no 
        values found besides unknown it will just return 'None'

        Inputs:
          - a dictionary of occurances of numeric data.  For example:
            {5:31, 8:4} indicating 31 occurances of 5 and 4 occurances of 8
        Outputs:
          - a single value - the mean of the inputs
        Test Coverage:
          - complete via test harness
    """
    count   = 0
    accum   = 0
    for value in values:
        try:
            accum += float(value) * float(values[value])
            count += float(values[value])
        except ValueError:      # catches occasional garbage data
            pass

    try:
        return accum / count
    except ZeroDivisionError:
        return None



class GetDictMedian(object):
    """ Calculates a median number for a dictionary of numbers.
        This has been designed as a class with a set of private functions mostly
        to help with testing.
    """
    def __init__(self):
        self.median = None


    def run (self, values):
        """ calculates the median on a list or dictionary of numbers
        """

        #---- catch empty inputs ------------------------------------------
        if not values:
            return None

        #---- first get everything into a list of tuples ------------------
        values_list  = self._get_tuple_list(values)

        #---- create all-numeric copy and get total count -----------------
        numeric_list = self._get_numeric_tuple_list(values_list)
        # just in case there was no numeric data in the inputs
        if not numeric_list:
            return None

        #---- sort by the keys --------------------------------------------
        sorted_list = sorted(numeric_list)

        tuple_count = self._get_tuple_list_count(numeric_list)

        #--- find middle subscripts ---------------------------------------
        low_sub, high_sub = self._get_median_subs(tuple_count)

        #--- find middle 2 scores: ----------------------------------------
        low_val  = self._get_median_keys(sorted_list, low_sub)
        high_val = self._get_median_keys(sorted_list, high_sub)

        #--- avg mid 2 scores (will be identical for odd counts) ----------
        try:
            self.median = (low_val + high_val) / 2
        except UnboundLocalError:   # empty input will have vals of None
            self.median = None

        return self.median


    def _get_tuple_list(self, values):

        return list(values.items())


    def _get_numeric_tuple_list(self, tuple_list):
        """ Makes a copy of a list of tuples with all data converted to 
            floats.
            Any conversion errors are addressed by dropping tuple out of list
            Input:
               - List of tuples  ex:  [('1',3),('9','2'),(5,'4')]
            Output:
               - list of tuples  ex:  [(1.0,3.0),(9.0,2.0),(5.0,4.0)]
        """
        numeric_list = []
        for key, count in tuple_list:
            try:
                pair = (float(key), float(count))
                numeric_list.append(pair)
            except ValueError:
                pass
        return numeric_list


    def _get_tuple_list_count(self, tuple_list):
        """ Returns a count of the number of pairs in the tuple_list
        """

        count = 0
        for pair in tuple_list:
            count += pair[1]

        return count

    def _get_median_subs(self, count):
        """ Identifies 2 middle number out of a count
            Inputs:
              - count:    assumed to be the length of a list
            Outputs:
              - low_sub:   the lower of the two numbers, offset from 0
              - high_sub:  the higher of the two numbers, offset from 0
            Test Coverage:
              - complete via test harness
        """
        if count <= 0:
            return 0, 0

        middle  = count // 2
        if count % 2 == 1:
            low_sub  = middle
            high_sub = middle
        else:
            low_sub  = middle - 1
            high_sub = middle

        return low_sub, high_sub


    def _get_median_keys(self, sorted_tuples, sub):
        """ Determines middle keys in a list of sorted tuples.
            - Dependencies:
                - must be 2 items per tuple
                - list must be sorted by first element of each tuple
                - sub must be validated against list - and exist
            - inputs:
                - sorted tuple:  [(3,2),(4,3),(5,2)]
                - sub:  A reference to an occurance of a key (NOT A TUPLE),
                        since the second value in the tuple is the count, a 3
                        would refer to the 4 in the second tuple above.
                     - ex: 3
            - outputs:
                - key:  4
        """
        accum = 0
        sub  += 1  # need to adjust offset from zero to tuple counts
        for key, count in sorted_tuples:
            accum += count
            if accum >= sub:
                return key

