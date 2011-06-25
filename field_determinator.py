#!/usr/bin/env python2.7
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldTyper   - class runs all checks on all fields
      get_field_type()
      get_type()
      is_timestamp() - determines if arg is a timestamp of some type
      is_float()   - determines if arg is a number
      is_integer() - determines if arg is a number
      is_string()  - determines if arg is a string
      get_case()   - determines case of input list or dictionary
      get_min()
      get_max()
      get_median()
    Todo:
      - change get_types to consider whatever has 2 STDs 
      - replace get_types freq length logic with something that says, if all types
        are basically numic, choose float
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


DATE_MIN_EPOCH_DEFAULT = 315561661     # 1980-01-01 01:01:01
DATE_MAX_EPOCH_DEFAULT = 1893484861    # 2030-01-01 01:01:01
DATE_MAX_LEN           = 26
DATE_INVALID_CHARS = ['`','`','!','@','#','$','%','^','&','*','(',')',
                      '_','+','=','[','{','}','}','|',
                      ';','"',"'",'<','>','?',
                      'q','z','x']
DATE_FORMATS = [ # <scope>, <pattern>, <format>
                ("year",   "YYYY",           "%Y"),
                ("month",  "YYYYMM",         "%Y%m"),
                ("month",  "YYYY-MM",        "%Y-%m"),
                ("month",  "YYYYMM",         "%Y%m"),
                ("day",    "YYYYMMDD",       "%Y%m%d"),
                ("day",    "YYYY-MM-DD",     "%Y-%m-%d"),
                ("day",    "DD/MM/YY",       "%d/%m/%y"),
                ("day",    "DD-MM-YY",       "%d-%m-%y"),
                ("day",    "MM/DD/YY",       "%m/%d/%y"),
                ("day",    "MM-DD-YY",       "%m-%d-%y"),
                ("day",    "MM/DD/YYYY",     "%m/%d/%Y"),
                ("day",    "MM-DD-YYYY",     "%m-%d-%Y"),
                ("day",    "DD/MM/YYYY",     "%d/%m/%Y"),
                ("day",    "DD-MM-YYYY",     "%d-%m-%Y"),
                ("day",    "MON DD,YYYY",    "%b %d,%Y"),
                ("day",    "MON DD, YYYY",   "%b %d, %Y"),
                ("day",    "MONTH DD,YYYY",  "%B %d,%Y"),
                ("day",    "MONTH DD, YYYY", "%B %d, %Y"),
                ("day",    "DD MON,YYYY",    "%d %b,%Y"),
                ("day",    "DD MON, YYYY",   "%d %b, %Y"),
                ("day",    "DD MONTH,YYYY",  "%d %B,%Y"),
                ("day",    "DD MONTH, YYYY", "%d %B, %Y"),
                ("hour",   "YYYY-MM-DD HH",  "%Y-%m-%d %H"),
                ("hour",   "YYYY-MM-DD-HH",  "%Y-%m-%d-%H"),
                ("minute", "YYYY-MM-DD HH:MM", "%Y-%m-%d %H:%M"),
                ("minute", "YYYY-MM-DD-HH.MM", "%Y-%m-%d-%H.%M"),
                ("second", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S"),
                ("second", "YYYY-MM-DD-HH.MM.SS", "%Y-%m-%d-%H.%M.%S"),
                # ".<microsecond>" at end is manually handled below
                ("microsecond", "YYYY-MM-DD HH:MM:SS", "%Y-%m-%d %H:%M:%S") ]


class FieldTyper(object):
    """ Examines ALL fields within a file
        Output structures:
          - self.field_names  - dictionary with fieldnumber key
          - self.field_types  - dictionary with fieldnumber key
          - self.field_min    - dictionary with fieldnumber key
          - self.field_max    - dictionary with fieldnumber key
          - self.field_mean   - dictionary with fieldnumber key
          - self.field_median - dictionary with fieldnumber key
          - self.field_case   - dictionary with fieldnumber key
    """

    def __init__(self        , 
                 filename    , 
                 format_type , 
                 field_cnt   ,
                 has_header  ,
                 dialect):
        self.filename            = filename
        self.format_type         = format_type
        self.field_cnt           = field_cnt
        self.has_header          = has_header
        self.dialect             = dialect

        #--- public field dictionaries - organized by field_number --- #
        self.field_names         = {}
        self.field_types         = {}
        self.field_min           = {}
        self.field_max           = {}
        self.field_mean          = {}   
        self.field_median        = {}  
        self.field_case          = {}

        #--- public field frequency distributions - organized by field number
        #--- each dictionary has a collection within it:
        self.field_freqs         = {}  # includes unknown values     
 


    def analyze_fields(self, field_number):
        """ Determines types & names of fields
        """
        
        for f_no in range(self.field_cnt):
            if field_number:
               if f_no <> field_number:
                  continue

            print
            print 'Analyzing field: %d' % f_no 

            self.field_names[f_no]   = get_field_names(self.filename, 
                                           f_no,
                                           self.has_header,
                                           self.dialect.delimiter)

            self.field_freqs[f_no]   = self._get_field_freq(self.filename, 
                                           f_no, 
                                           self.has_header,
                                           self.dialect.delimiter)

            self.field_types[f_no]   = get_field_type(self.field_freqs[f_no])
            self.field_mean[f_no]    = get_mean(self.field_freqs[f_no])
            self.field_median[f_no]  = get_median(self.field_freqs[f_no])
            self.field_max[f_no]     = get_max(self.field_types[f_no],
                                               self.field_freqs[f_no])
            self.field_min[f_no]     = get_min(self.field_types[f_no],
                                               self.field_freqs[f_no])
            self.field_case[f_no]    = get_case(self.field_types[f_no],
                                                self.field_freqs[f_no])


    def _get_field_freq(self, 
                         filename, 
                         field_number,
                         has_header,
                         field_delimiter):
        """ Notes:
            - might want to use csv sniffer data for handling quoting, but
              it seems to work ok so far.
        """
        MAX_FREQ_SIZE = 10000

        freq  = collections.defaultdict(int)
        rec_cnt = 0
        for rec in csv.reader(open(filename,'r'), delimiter=field_delimiter):
            rec_cnt += 1
            if rec_cnt == 1 and has_header:
                continue
            freq[rec[field_number]] += 1
            if len(freq) > MAX_FREQ_SIZE:
                print 'WARNING: freq is getting too large - will truncate'
                break
        
        return freq


    def get_known_values(self, fieldno):
       """ returns a frequency-distribution dictionary that is the 
           self.field_freqs with unknown values removed.
       """

       return [val for val in self.field_freqs[fieldno]
               if is_unknown_value(val) is False]


    def get_top_freq_values(self,
                            fieldno,
                            limit=None):
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
                     
        sort_list = sorted(self.field_freqs[fieldno], 
                           key=self.field_freqs[fieldno].get)
        sub           = len(sort_list) - 1
        count         = 0
        rev_sort_list = []
        while sub > 0:
            freq  = self.field_freqs[fieldno][sort_list[sub]]
            rev_sort_list.append([sort_list[sub], freq])
            count += 1
            sub   -= 1
            if limit is not None:
                if count >= limit:
                    break

        return rev_sort_list



def get_field_type(values):
    """ Figures out the type of every item in the value list or dictionary,
        then consolidates that into a single output type.
        Test Coverage:
          - complete via test harness
    """  
    type_freq  = collections.defaultdict(int)
    field_type = None

    # count occurances of each case type in values:
    for key in values:
        type_freq[get_type(key)] += 1

    # create consolidated array:
    if len(type_freq)  == 1:
        key         = type_freq.keys()
        field_type = key[0]
    elif len(type_freq) == 2  \
    and 'unknown' in type_freq:
        if 'string'    in type_freq:
            field_type = 'string'
        elif 'number'  in type_freq:
            field_type = 'number'
        elif 'integer' in type_freq:
            field_type = 'integer'
        elif 'float'   in type_freq:
            field_type = 'float'
        else:
            field_type = 'unknown'
    elif len(type_freq) == 2:
        if 'float'     in type_freq  \
        and 'integer'  in type_freq:
            field_type  = 'float'
    elif len(type_freq) == 3:
        if  ('unknown' in type_freq  \
        and 'float'    in type_freq  \
        and 'integer'  in type_freq):
            field_type = 'float'
    elif len(type_freq) == 4:
        if  ('unknown' in type_freq  \
        and 'timestamp' in type_freq \
        and 'float'    in type_freq  \
        and 'integer'  in type_freq):
            field_type = 'float'
    else:
        # if one value is far more common then the other, select it:
        # add code here
        # otherwise, go with unknown:
        field_type = 'unknown'

    return field_type



def get_type(value):
    """ accepts a value and returns its basic type:
        - int
        - string
        - timestamp
        - time
        Test Coverage:
          - complete via test harness
    """
    dtc_status, dtc_scope, dtc_pattern = is_timestamp(value)
    if dtc_status:
        return 'timestamp'
    elif is_unknown_value(value):
        return 'unknown'
    elif is_float(value):
        return 'float'
    elif is_integer(value):
        return 'integer'
    #elif field_typer.is_date(value):
    #    return 'date'
    #elif field_typer.is_time(value):
    #    return 'time'
    elif is_string(value):
        return 'string'
    else:
        return 'string'


def get_field_names(filename, 
                    field_number,
                    has_header,
                    field_delimiter):
    """ Determines names of fields 
        Notes:
          - It should not be possible to process an empty file - since the 
            file_detminator should catch that first.
    """
    in_file   = open(filename, "r")
    in_rec    = in_file.readline()
    in_file.close()

    if not in_rec:
        return None

    fields    = in_rec[:-1].split(field_delimiter)

    if has_header is True:     # get field names from header record
        field_name = fields[field_number]
    else:
        field_name = 'field_num_%d' % field_number
    return field_name




def get_mean(values):
    """ Returns the maximum value found for input dictionary or list
        Ignores unknown values, if no values found besides unknown it will
        just return 'None'
        Test Coverage:
          - complete via test harness
    """
    clean_list = []
    for val in values:
        if is_unknown_value(val):
            continue
        try:
            clean_list.append(float(val))
        except TypeError:
            continue
        except ValueError:    # catches non-numbers
            continue
       
    try:
        mean = sum(clean_list) / len(clean_list)
    except ZeroDivisionError:
        return None
    else:
        return mean


def get_median(values):
    """ Returns the median value found for input dictionary or list
        Ignores unknown values, if no values found besides unknown it will
        just return 'None'
        Test Coverage:
          - complete via test harness
    """
    clean_list = []
    for val in values:
        if is_unknown_value(val):
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
           

def get_max(type, values):
    """ Returns the maximum value found for input dictionary or list
        Ignores unknown values, if no values found besides unknown it will
        just return 'None'
        Test Coverage:
          - complete via test harness
    """
    assert(type in ['integer', 'float', 'string', 'timestamp', None])

    if type == 'integer':
       clean_values = [int(val) for val in values 
                       if is_unknown_value(val) is False]
    elif type == 'float':
       clean_values = [float(val) for val in values 
                       if is_unknown_value(val) is False]
    else:
       clean_values = [val for val in values 
                       if is_unknown_value(val) is False]

    try:
        if type in ['integer','float']:
           return str(max(clean_values))
        else:
           return max(clean_values)
    except ValueError:
        return None


def get_min(type, values):
    """ Returns the minimum value found for input dictionary or list
        Ignores unknown values, if no values found besides unknown it will
        just return 'None'
        Test Coverage:
          - complete via test harness
    """
    assert(type in ['integer', 'float', 'string', 'timestamp', None])
    if type == 'integer':
       clean_values = [int(val) for val in values 
                       if is_unknown_value(val) is False]
    elif type == 'float':
       clean_values = [float(val) for val in values 
                       if is_unknown_value(val) is False]
    else:
       clean_values = [val for val in values 
                       if is_unknown_value(val) is False]

    try:
        if type in ['integer','float']:
           return str(min(clean_values))
        else:
           return min(clean_values)
    except ValueError:
        return None


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
        if is_unknown_value(key):
            freq['unk']    += 1
        elif is_integer(key):
            freq['number'] += 1
        elif is_float(key):
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


def is_string(value):
    """ Returns True if the value is a string, subject to false-negatives
        if the string is all numeric.
        'b'      is True
        ''       is True
        ' '      is True
        '$3'     is True
        '4,333'  is True
        '33.22'  is False
        '3'      is False
        '-3'     is False
        3        is False
        3.3      is False
        None     is False
        Test coverage:
          - complete, via test harness
    """
    try:                    # catch integers & floats
        float(value)
        return False
    except TypeError:       # catch None
        return False
    except ValueError:      # catch characters
        return True



def is_integer(value):
    """ Returns True if the input consists soley of digits and represents an
        integer rather than character data or a float.
        '3'       is True
        '-3'      is True
        3         is True
        -3        is True
        3.3       is False
        '33.22'   is False
        '4,333'   is False
        '$3'      is False
        ''        is False
        'b'       is False
        None      is False
        Test coverage:
          - complete, via test harness
    """
    try:
        i            = float(value)
        fract, integ = math.modf(i)
        if fract > 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False


def is_float(value):
    """ Returns True if the input consists soley of digits and represents a
        float rather than character data or an integer.
        44.55   is True
        '33.22' is True
        6       is False
        '3'     is False
        '-3'    is False
        '4,333' is False
        '$3'    is False
        ''      is False
        'b'     is False
        None    is False
        Test coverage:
          - complete, via test harness
    """
    try:
        i            = float(value)
        fract, integ = math.modf(i)
        if fract == 0:
            return False
        else:
            return True
    except ValueError:
        return False
    except TypeError:
        return False



def is_unknown_value(value):
    """ Returns True if the value is a common unknown indicator:
        ''        is True
        ' '       is True
        'na'      is True
        'NA'      is True
        'n/a'     is True
        'N/A'     is True
        'unk'     is True
        'unknown' is True
        '3'       is False
        '-3'      is False
        '33.22'   is False
        '4,333'   is False
        '$3'      is False
        'b'       is False
        3         is False
        3.3       is False
        None      is False
        Test coverage:
          - complete, via test harness
    """
    unk_vals = ['na', 'n/a', 'unk', 'unknown', '']
    try:
        if value.strip().lower() in unk_vals:
            return True
        else:
            return False
    except AttributeError:
        return False
    except TypeError:
        return False
       

def is_timestamp(time_str):
    """ Determine if arg is a timestamp and if so what format

        Args:
           time_str - character string that may be a date, time, epoch or combo
        Returns:
           status   - True if date/time False if not
           scope    - kind of timestamp
           pattern  - date mask

        To do:
           - consider overrides to default date min & max epoch limits
           - consider consolidating epoch checks with rest of checks
    """
    non_date = (False, None, None)
    if len(time_str) > DATE_MAX_LEN:
       return non_date
   
    try:
       float_str = float(time_str)
       if DATE_MIN_EPOCH_DEFAULT < float_str < DATE_MAX_EPOCH_DEFAULT:
           t_date = datetime.datetime.fromtimestamp(float(time_str))
           return True, 'second', 'epoch'
    except ValueError:
       pass

    for scope, pattern, format in DATE_FORMATS:
        if scope == "microsecond":
            # Special handling for microsecond part. AFAIK there isn't a
            # strftime code for this.
            if time_str.count('.') != 1:
                continue
            time_str, microseconds_str = time_str.split('.')
            try:
                microsecond = int((microseconds_str + '000000')[:6])
            except ValueError:
                continue
        try:
            # This comment here is the modern way. The subsequent two
            # lines are for Python 2.4 support.
            t_date = datetime.datetime.strptime(time_str, format)
            ## old way:
            ##t_tuple = time.strptime(time_str, format)
            ##t_date  = datetime.datetime(*t_tuple[:6])
        except ValueError:
            pass
        else:
            if scope == "microsecond":
                t_date = t_date.replace(microsecond=microsecond)
            return True, scope, pattern
    else:
        return False,  None, None

