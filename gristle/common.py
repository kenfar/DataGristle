#!/usr/bin/env python
""" Used to hold all common  general-purpose functions and classes

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

from __future__ import division

#--- standard modules ------------------


def get_common_key(count_dict):
    """  Provides the most common key in a dictionary as well as its frequency
         expressed as a percentage.  For example:
         cd = ['car':    7
               'boat':  30
               'truck':  8
               'plane':  5
         print most_common_key(cd)
         >>> boat, 60
    """
    sorted_keys  = (sorted(count_dict, key=count_dict.get))
    total_values = sum(count_dict.itervalues())
    most_common_key       = sorted_keys[-1]
    most_common_key_value = count_dict[sorted_keys[-1]]
    most_common_pct       = most_common_key_value / total_values 
    return most_common_key, most_common_pct



def coalesce(default, *args):
    """ Returns the first non-None value.
        If no non-None args exist, then return default.
    """
    for arg in args:
        if arg not in (None, "'None'", 'None'):
            return arg
    return default



def get_common_key(count_dict):
    """  Provides the most common key in a dictionary as well as its frequency
         expressed as a percentage.  For example:
         cd = ['car':    7
               'boat':  30
               'truck':  8
               'plane':  5
         print most_common_key(cd)
         >>> boat, 60
    """
    sorted_keys  = (sorted(count_dict, key=count_dict.get))
    total_values = sum(count_dict.itervalues())
    most_common_key       = sorted_keys[-1]
    most_common_key_value = count_dict[sorted_keys[-1]]
    most_common_pct       = most_common_key_value / total_values 
    return most_common_key, most_common_pct



