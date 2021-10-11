#!/usr/bin/env python
""" Applies a list of python slicing specifications to a number to determine if
    that number meets the specifications or not.

    Typical Usage:
        >>> sp = location_slicer.SpecProcessor(['1','5','10:20','70:-1'], 'rec incl')
        >>> sp.spec_adjuster(loc_max=80)
        >>> sp.spec_evaluator(5)
        True
        >>> sp.spec_evaluator(0)
        False
        >>> sp.spec_evaluator(15)
        True
        >>> sp.spec_evaluator(78)
        True
        >>> sp.spec_evaluator(79)
        False

    A few notes about the logic:
        - specs are provided as text items within a list
        - each spec item may take the form of:
            - specific number - to qualify the location must match this exactly
            - range - to qualify the location must be >= to minimum and < maximum
        - numbers omitted default to end of record in that direction:
            - ':50' - is from 0 to 50
            - '20:' is from 20 to end of record
        - negative values are adjusted to their positive values

    This source code is protected by the BSD license.  See the file "LICENSE"
    in the source code root directory for the full language or refer to it here:
       http://opensource.org/licenses/BSD-3-Clause
    Copyright 2011-2021 Ken Farmer
"""

import copy
from dataclasses import dataclass
from pprint import pprint as pp
import re
import sys
from typing import List, Dict, Tuple, Union, Any, Optional

import datagristle.common as comm
import datagristle.csvhelper as csvhelper

MAX_MEM_RECS = 100000 # limits size of recs in memory



class SpecProcessor(object):

    def __init__(self,
                 raw_specs: List[str],
                 header: Optional[csvhelper.Header],
                 infile_item_count: int,
                 max_mem_recs: int = MAX_MEM_RECS) -> None:
        """
        Header: Is always expected for column specs that read from files, but will just be None
                for columns specs for stdin inputs.  Is also always None for record specs.
        """

        self.raw_specs = raw_specs           # spec with names, ranges, negatives
        self.numeric_specs: List[str] = []   # spec with names converted to positions
        self.positive_specs: List[str] = []  # spec with negatives converted
        self.expanded_specs: Optional[List[int]] = []    # spec ranges converted to offsets
        self.header = header
        self.max_mem_recs = max_mem_recs

        self.numeric_specs = self._spec_name_translater(self.raw_specs, header)

        if spec_has_negatives(self.numeric_specs):
            self.positive_specs = self._spec_negative_translator(infile_item_count)
        else:
            self.positive_specs = copy.copy(self.numeric_specs)

        self._spec_validator(self.numeric_specs)      # will raise exceptions if any exist

        self.expanded_specs = self._spec_range_expander(infile_item_count, max_mem_recs)


    def _spec_name_translater(self,
                              spec: List[str],
                              header: Optional[csvhelper.Header]) -> List[str]:
        """ Reads through a single spec (ie, record inclusion spec, column
            exclusion spec, etc) and remaps any column names to their position
            offsets.
            Inputs:
                - spec, ex: [' 1',' -3',' 4:7', ' home_state', ' last_name:']
                - header object
            Outputs:
                - a numeric-only spec, ex: ['1','-3','4:7','9','12:']
        """
        if header is None:
            return spec

        num_spec = []
        for item in spec:
            new_parts = []
            for part in item.split(':'):
                part = part.strip()
                if part is None or part == '':
                    new_parts.append(part)
                elif comm.isnumeric(part):
                    new_parts.append(part.strip())
                else:
                    try:
                        new_parts.append(str(header.get_field_position(part)))
                    except KeyError:
                        comm.abort(f'Error: Invalid string in spec: {part}',
                                    f'Not in header list: {header.field_names}')
            num_spec.append(':'.join(new_parts))

        return num_spec


    def _spec_validator(self,
                        spec: List[str]) -> bool:
        """ Checks for any invalid specifications.
        """
        if not spec_is_sequence(spec):
            raise ValueError('spec argument is not a sequence object')

        def _is_invalid_part(part: str) -> bool:
            try:
                int(part)
            except (TypeError, ValueError):
                return True
            return False

        for item in spec:
            parts = item.split(':')
            if len(parts) == 1:
                if _is_invalid_part(parts[0]):
                    raise ValueError('spec is non-numeric')
            elif len(parts) == 2:
                if parts[0] != '' and _is_invalid_part(parts[0]):
                    raise ValueError('spec is non-numeric')
                if parts[1] != '' and _is_invalid_part(parts[1]):
                    raise ValueError('spec is non-numeric')
                if (parts[0] != '' and parts[1] != ''):
                    if int(parts[1]) >= 0:
                        if int(parts[0]) >= int(parts[1]):
                            raise ValueError('spec is an invalid range')
            elif len(parts) > 2:
                raise ValueError('spec has too many parts')
        return True


    def _spec_negative_translator(self,
                                  infile_item_count: int) -> List[str]:
        """ Reads through a single spec (ie, record inclusion spec, column
            exclusion spec, etc) and remaps any negative values to their positive
            equiv.
            Inputs:
                - infile_item_count: the max number of items to apply the spec to.  The
                  location starts at an offset of 0.  Additionally:
                  - for a col spec this is the number of cols in a record
                  - for a row spec this is the number of recs in the file
            Outputs:
                - none
        """
        positive_spec: List[str] = []
        for item in self.numeric_specs:
            parts = item.split(':')
            new_parts = []
            for part in parts:
                if part is None or part == '':
                    new_parts.append(part)
                else:
                    if int(part) < 0:
                        new_parts.append(str(infile_item_count+ int(part) + 1 ))
                    else:
                        new_parts.append(part)
            positive_spec.append(':'.join(new_parts))
        return positive_spec


    def _spec_range_expander(self,
                             infile_item_count: int,
                             max_mem_recs: int) -> Optional[List[int]]:
        ordered_spec = []
        for item in self.positive_specs:
            parts = item.split(':')
            if len(parts) == 1:
                ordered_spec.append(int(parts[0]))
            elif len(parts) == 2:
                start_part = int(parts[0] if parts[0] != '' else 0)
                stop_part = int(parts[1] if parts[1] != '' else infile_item_count+1)
                for part in range(start_part, stop_part):
                    ordered_spec.append(int(part))
            if len(ordered_spec) > max_mem_recs:
                sys.stderr.write('WARNING: insufficient memory - may be slow\n')
                return None
        return ordered_spec


    def spec_evaluator(self, location: int) -> bool:
        """ Evaluates a location (column number or record number) against
            a specifications list.  Description:
               - uses the python string slicing formats to specify valid ranges
                (all offset from 0):
               - 4, 5, 9 = location 4, 5, and 9
               - 1:3     = location 1 & 2 (end - 1)
               - 5:      = location 5 to the end
               - :5      = location 0 to 4 (end - 1)
               - :       = all locations
               - template:  spec, spec, spec:spec, spec, spec:spec
               - example:   4,    8   , 10:14    , 21  , 48:55
               - The above example is stored in a five-element spec-list
            Input:
               - location:  a column or record number
            Output:
               - True if the number matches one of the specs
               - False if the number does not match one of the specs
               - False if the spec_list is empty
            To do:
               - support slice steps
        """
        if not self.positive_specs:
            # the self.positive_specs will often be None for 1-2 of the 4 specs.
            # ex: incl criteria provided (or defaulted to ':'), but if no
            # excl critieria provided it will be None.
            return False

        if any([self._spec_item_evaluator(x, int(location)) for x in self.positive_specs]):
            return True

        return False


    def _spec_item_evaluator(self, item: str, location: int) -> bool:
        """ evaluates a single item against a location
            inputs:
                - item in form of string like one of these:
                     - '5'
                     - '1:10'
                - location - an integer to be compared to item
            outputs:
                - True or False
        """
        if item == ':':
            return True
        else:
            parts =  item.split(':')
            if len(parts) == 1:
                if parts[0] == '' or int(parts[0]) != location:
                    return False
                else:
                    return True
            else:
                if ((parts[0] != '' and location < int(parts[0]))
                or ( parts[1] != '' and location >= int(parts[1]))):
                    return False
                else:
                    return True



def spec_has_negatives(spec: List[str]) -> bool:
    """ Checks for negative values in a single spec
    """
    for item in spec:
        if '-' in item:
            return True
    return False

def spec_has_unbounded_range(spec: List[str]) -> bool:
    """ Checks for unbounded outer range in a single spec
    """
    for item in spec:
        parts = item.split(':')
        if len(parts) == 2:
            if parts[1] == '':
                return True
    return False

def spec_is_sequence(spec: List[str]) -> bool:
    """ test whether or not a spec is a squence - list or tuple
            input:  val
            output:  True or False
    """
    if isinstance(spec, (list, tuple)):
        return True
    else:
        return False




