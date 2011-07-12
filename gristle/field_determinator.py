#!/usr/bin/env python
""" Purpose of this module is to identify the types of fields
    Classes & Functions Include:
      FieldDeterminator   - class runs all checks on all fields
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

import field_type   as typer
import field_math   as mather
import field_misc   as miscer


#--- CONSTANTS -----------------------------------------------------------



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
        self.field_max_length    = {}
        self.field_min_length    = {}
        self.field_trunc         = {}

        #--- public field frequency distributions - organized by field number
        #--- each dictionary has a collection within it:
        self.field_freqs         = {}  # includes unknown values     
 


    def analyze_fields(self, field_number=None):
        """ Determines types, names, and characteristics of fields.

            Inputs:
               - field_number - if None, then analyzes all fields, otherwise
                 analyzes just the single field (based on zero-offset)
            Outputs:
               - populates public class structures
        """
        
        print 'Field Analysis Progress: '
        for f_no in range(self.field_cnt):
            if field_number:
                if f_no != field_number:
                    continue

            print '   Analyzing field: %d' % f_no 

            self.field_names[f_no]   = miscer.get_field_names(self.filename, 
                                           f_no,
                                           self.has_header,
                                           self.dialect.delimiter)

            (self.field_freqs[f_no],
            self.field_trunc[f_no])  = miscer.get_field_freq(self.filename, 
                                           f_no, 
                                           self.has_header,
                                           self.dialect.delimiter)

            self.field_types[f_no]   = typer.get_field_type(self.field_freqs[f_no])
            self.field_max[f_no]     = miscer.get_max(self.field_types[f_no],
                                               self.field_freqs[f_no])
            self.field_min[f_no]     = miscer.get_min(self.field_types[f_no],
                                               self.field_freqs[f_no])
            self.field_case[f_no]    = miscer.get_case(self.field_types[f_no],
                                                self.field_freqs[f_no])
            self.field_min_length[f_no] = miscer.get_min_length(self.field_freqs[f_no])
            self.field_max_length[f_no] = miscer.get_max_length(self.field_freqs[f_no])

            if self.field_types[f_no] in ['integer','float']:
                self.field_mean[f_no]   = mather.get_mean(self.field_freqs[f_no])
                self.field_median[f_no] = mather.GetDictMedian().run(self.field_freqs[f_no])

    def get_known_values(self, fieldno):
        """ returns a frequency-distribution dictionary that is the 
            self.field_freqs with unknown values removed.
        """

        return [val for val in self.field_freqs[fieldno]
                if typer.is_unknown(val) is False]


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


