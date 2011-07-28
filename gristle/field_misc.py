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
"""
from __future__ import division
import collections
import csv
import fileinput

import field_type as typer

#--- CONSTANTS -----------------------------------------------------------

MAX_FREQ_SIZE_DEFAULT  = 10000     # limits entries within freq dictionaries


def get_field_names(filename, 
                    field_number,
                    has_header,
                    field_delimiter,
                    rec_delimiter,
                    field_cnt):
    """ Determines names of fields 
    """
    #print 'get_field_names - has_header: %s' % has_header
    bad_rec = False
    for rec in fileinput.input(filename):
        if rec_delimiter:
            partial_rec = rec[:-1].split(rec_delimiter)[0]
        else:
            partial_rec = rec[:-1]
        #print partial_rec
        fields = partial_rec.split(field_delimiter)
        if len(fields) != field_cnt:
            bad_rec = True
            print 'bad_rec! len: %d, expected: %d' % (len(fields), field_cnt)
        break # we're only after the first record
    fileinput.close()
    if not fields:
        print 'Error: Empty file'
        return None

    if has_header \
    and not bad_rec:
        field_name = fields[field_number]
    else:
        field_name = 'field_num_%d' % field_number
    return field_name



def get_case(field_type, values):
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
        Test coverage:
          - complete, via test harness
    """
    freq = collections.defaultdict(int)
    case = None

    if field_type != 'string':
        return 'n/a'

    # count occurances of each case field_type in values:
    for key in values:
        if typer.is_unknown(key):
            freq['unk']    += 1
        elif typer.is_integer(key):     # will be ignoring these
            freq['number'] += 1
        elif typer.is_float(key):       # will be ignoring these
            freq['number'] += 1
        elif key.islower():
            freq['lower'] += 1
        elif key.isupper():
            freq['upper'] += 1
        else:
            freq['mixed'] += 1

    # evaluate frequency distribution:
    if 'mixed' in freq:
        case = 'mixed'
    elif ('lower' in freq and 'upper' not in freq):
        case = 'lower'
    elif ('lower' not in freq and 'upper' in freq):
        case = 'upper'
    elif ('lower' in freq and 'upper' in freq):
        case = 'mixed'
    else:
        case = 'unknown'

    return case


def get_field_freq(filename, 
                   field_number,
                   has_header,
                   field_delimiter,
                   rec_delimiter,
                   field_cnt,
                   max_freq_size=MAX_FREQ_SIZE_DEFAULT):
    """ Collects a frequency distribution for a single field by reading
        the file provided.
    """
    #print 'field_delimiter: %s' % field_delimiter
    freq        = collections.defaultdict(int)
    rec_cnt     = 0
    bad_rec_cnt = 0
    truncated   = False
    #print 'field_delimiter: %s' % field_delimiter
    if len(field_delimiter) == 1:
        for fields in csv.reader(open(filename,'r'), delimiter=field_delimiter):
            rec_cnt += 1
            if rec_cnt == 1 and has_header:
                continue
            if len(fields) != field_number:
                bad_rec_cnt += 1
                continue
            freq[fields[field_number]] += 1
            if len(freq) >= max_freq_size:
                print '      WARNING: freq dict is too large - will trunc'
                truncated = True
                break
    else:
        for rec in fileinput.input(filename):
            if rec_delimiter:
               x = rec[:-1].split(rec_delimiter)
               partial_rec = x[0]
            else:
               partial_rec = rec[:-1]
            fields = partial_rec.split(field_delimiter)
            #print fields
            rec_cnt += 1
            if rec_cnt == 1 and has_header:
                continue
            if len(fields) != field_cnt:
                bad_rec_cnt += 1
                continue
            try:
                freq[fields[field_number]] += 1
            except IndexError:
                print('IndexError')
                print('Field Number: %d' % field_number)
                print(fields)
                print(rec)
                print('rec_cnt: %d' % rec_cnt)
                print('field_cnt:    %d' % field_cntr)
                print('field_len:    %d' % len(fields))
            if len(freq) >= max_freq_size:
                print '      WARNING: freq dict is too large - will trunc'
                truncated = True
                break
        fileinput.close()
   
        
    return freq, truncated



def get_min(value_type, values):
    """ Returns the minimum value of the input.  Ignores unknown values, if 
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single maximum value

        Test Coverage:
          - complete via test harness
    """
    assert(value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None])
    if value_type == 'integer':
        try:
            y = [int(val) for val in values if not typer.is_unknown(val)]
        except ValueError:
            print('ERROR: invalid non-numeric value')
            print values
            return None
    elif value_type == 'float':
        y = [float(val) for val in values if not typer.is_unknown(val)]
    else:
        y = [val for val in values if not typer.is_unknown(val)]

    try:
        if value_type in ['integer','float']:
            return str(min(y))
        else:
            return min(y)
    except ValueError:
        return None



def get_max(value_type, values):
    """ Returns the maximum value of the input.  Ignores unknown values, if 
        no values found besides unknown it will just return 'None'

        Inputs:
          - value_type - one of integer, float, string, timestap
          - dictionary or list of string values
        Outputs:
          - the single maximum value

        Test Coverage:
          - complete via test harness
    """
    assert(value_type in ['integer', 'float', 'string', 'timestamp', 'unknown', None])

    if value_type == 'integer':
        try:
           y = [int(val) for val in values if not typer.is_unknown(val)]
        except ValueError:
           print 'ERROR: unexpected non-numeric value'
           print values
           return None
    elif value_type == 'float':
        y = [float(val) for val in values if not typer.is_unknown(val)]
    else:
        y = [val for val in values if not typer.is_unknown(val)]

    try:
        if value_type in ['integer','float']:
            return str(max(y))
        else:
            return max(y)
    except ValueError:
        return None



def get_max_length(values):
    """ Returns the maximum length value of the input.   If
        no values found besides unknown it will just return 'None'

        Inputs:
          - dictionary or list of string values
        Outputs:
          - the single maximum value
    """
    max_length = 0

    for value in values:
        if not typer.is_unknown(value):
            if len(value) > max_length:
                max_length = len(value)

    return max_length



def get_min_length(values):
    """ Returns the minimum length value of the input.   If
        no values found besides unknown it will just return 'None'

        Inputs:
          - dictionary or list of string values
        Outputs:
          - the single minimum value
    """
    min_length = 999999

    for value in values:
        if not typer.is_unknown(value):
            if len(value) < min_length:
                min_length = len(value)

    return min_length




