#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldDeterminator   - class runs all checks on all fields
    Todo:
      - change get_types to consider whatever has 2 STDs
      - replace get_types freq length logic with something that says,
        if all types are basically numic, choose float
      - add quartiles, variances and standard deviations
      - add statistical analysis for data quality
      - add histogram to automatically bucketize data
      - consistency metric
      - leverage list comprehensions more
      - consider try/except in get_min() & get_max() int/float conversion
      - change returned data format to be based on field

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2021 Ken Farmer
"""
from operator import itemgetter
from pprint import pprint as pp
import time
from typing import Optional, List, Tuple, Dict, Any

import datagristle.common as common
import datagristle.configulator as configulator
import datagristle.csvhelper as csvhelper
import datagristle.field_type as typer
import datagristle.field_math as mather
import datagristle.field_misc as miscer

#------------------------------------------------------------------------------
# override miscer.get_field_freq max dictionary size defaults:
# The sizes are based on these assumptions:
#   Single col with 10 million unique items, average item length of 20 bytes
#   plus a hashed version of item key, plus two pointers.  That's about 40
#   bytes per entry, or 400 MBytes maximum in this case.
#   Multi-column needs to be more conservative since there could be 10,20, or
#   80 different columns.  So it's limited to 1/10th the number of items.
#------------------------------------------------------------------------------
MAX_FREQ_SINGLE_COL_DEFAULT = 10000000 # ex: 1 col, 10 mil items with 20 byte key = ~400 MB
MAX_FREQ_MULTI_COL_DEFAULT  = 1000000  # ex: 10 cols, each with 1 mil entries & 20 byte key = ~400 MB total


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

        # xperimental
        self.field_freq: Dict[int, Dict[Any, int]] = {i:{} for i in range(self.field_cnt)}
        self.field_min: Dict[int, Optional[Any]] = {}  # all data
        self.field_max: Dict[int, Optional[Any]] = {}  # all data

        #--- public field dictionaries - organized by field_number --- #
        # every field should have a key in every one of these dictionaries
        # but if the dictionary doesn't apply, then the value may be None
        self.field_names:       Dict[int, str] = {}  # all data
        self.field_types:       Dict[int, str] = {}  # all data
        self.field_trunc:       Dict[int, bool] = {i:False for i in range(self.field_cnt)}   # all data
        self.field_rows_invalid: Dict[int, int] = {}  # all data

        self.field_mean:        Dict[int, Optional[float]] = {}  # only for numeric data
        self.field_median:      Dict[int, Optional[float]] = {}  # only for numeric data
        self.variance:          Dict[int, Optional[float]] = {}  # only for numeric data
        self.stddev:            Dict[int, Optional[float]] = {}  # only for numeric data
        self.field_decimals:    Dict[int, Optional[int]] = {}    # only for numeric data

        self.field_case:        Dict[int, Optional[str]] = {}  # only for string data
        self.field_max_length:  Dict[int, Optional[int]] = {}  # only for string data
        self.field_min_length:  Dict[int, Optional[int]] = {}  # only for string data
        self.field_mean_length: Dict[int, Optional[float]] = {}  # only for string data

        #--- public field frequency distributions - organized by field number
        #--- each dictionary has a collection within it:
        #self.field_freqs:       Dict[int, Dict[Any, int]] = {}  # includes unknown values

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


        #---- field_freqs --------------------------------
        for rec in self.input_handler:
            self._get_field_freqs(rec)
            if read_limit > -1 and self.input_handler.rec_cnt >= read_limit:
                for f_no in range(self.field_cnt):
                    self.field_trunc[f_no] = True
                break
        field_freq_list = list(self.field_freq.items())

        self._get_field_types(field_types_overrides)
        self._get_field_name()
        self._get_field_minmax()



        for f_no in self.field_freq.keys():
            if self.field_types[f_no] == 'string':
                self.field_case[f_no] = miscer.get_case(self.field_types[f_no], self.field_freq[f_no])
                self.field_min_length[f_no] = miscer.get_min_length(self.field_freq[f_no].items())
                self.field_max_length[f_no] = miscer.get_max_length(self.field_freq[f_no].items())
                self.field_mean_length[f_no] = mather.get_mean_length(self.field_freq[f_no].items())
            else:
                self.field_case[f_no] = None
                self.field_min_length[f_no] = None
                self.field_max_length[f_no] = None
                self.field_mean_length[f_no] = None


        for f_no in self.field_freq.keys():
            if self.field_types[f_no] in ('integer', 'float'):
                self.field_mean[f_no] = mather.get_mean(self.field_freq[f_no].items())
                self.field_median[f_no] = mather.get_median(self.field_freq[f_no].items())
                (self.variance[f_no], self.stddev[f_no])   \
                   = mather.get_variance_and_stddev(self.field_freq[f_no].items(), self.field_mean[f_no])
                self.field_decimals[f_no] = mather.get_max_decimals(self.field_freq[f_no].items(), self.field_types[f_no])
            else:
                self.field_mean[f_no] = None
                self.field_median[f_no] = None
                self.variance[f_no] = None
                self.stddev[f_no] = None
                self.field_decimals[f_no] = None


    def _get_field_freqs(self,
                         rec):


        for field_number, key in enumerate(rec):

            if self.field_trunc.get(field_number):
                continue
            try:
                key = key.strip()
                if field_number not in self.field_freq:
                    self.field_freq[field_number] = {}
                self.field_freq[field_number][key] += 1
            except KeyError:
                self.field_freq[field_number][key] = 1
            except IndexError:
                try:
                    self.field_rows_invalid[field_number] +1
                except KeyError:
                    self.field_rows_invalid[field_number] +1
            except AttributeError as e: # quote_nonnumeric returns floats(!)
                if ("'float' object has no attribute 'strip'")  in repr(e):
                    if field_number not in self.field_freq:
                        self.field_freq[field_number] = {}
                    if rec[field_number] in self.field_freq[field_number]:
                        self.field_freq[field_number][rec[field_number]] += 1
                    else:
                        self.field_freq[field_number][rec[field_number]] = 1

            if self.max_items > -1 and len(self.field_freq[field_number]) >= self.max_items:
                print(f'    WARNING: freq dict is too large for field {field_number} - will stop adding to it')
                self.field_trunc[field_number] = True


    def _get_field_types(self,
                         field_types_overrides):

        for f_no in self.field_freq.keys():
            self.field_types[f_no] = typer.get_field_type(self.field_freq[f_no])
            if field_types_overrides:
                for col_no in field_types_overrides:
                    self.field_types[col_no] = field_types_overrides[col_no]
        if not self.field_types:
            common.abort('ERROR: self.field_types is EMPTY! aborting')

    def _get_field_name(self):
        if self.input_handler.header:
            self.field_names = self.input_handler.header
        else:
            filename = self.input_handler.files[0]
            self.field_names = miscer.get_field_names(filename, self.dialect)


    def _get_field_minmax(self):
        for f_no in self.field_freq.keys():
            self.field_max[f_no] = miscer.get_max(self.field_types[f_no], self.field_freq[f_no].items())
            self.field_min[f_no] = miscer.get_min(self.field_types[f_no], self.field_freq[f_no].items())


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




class IOErrorEmptyFile(IOError):
    """Error due to empty file
    """
    pass
