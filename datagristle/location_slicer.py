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
    """ Manages all types of specifications - inclusion or exclusion for rows & cols.

    That means, it translates the specs into useful structures, and supports the
    evaluation of col or row numbers aginst the specs.
    """

    def __init__(self,
                 raw_specs: List[str],
                 header: Optional[csvhelper.Header],
                 infile_item_count: int,
                 max_mem_recs: int = MAX_MEM_RECS) -> None:
        """
        Header: Is always expected for column specs that read from files, but will just be None
                for columns specs for stdin inputs.  Is also always None for record specs.
        """
        self.clean_specs: List[Tuple[str, str]] \
            = self._specs_cleaner(raw_specs, header, infile_item_count)

        self.expanded_specs: Optional[List[int]] \
            = self._specs_range_expander(infile_item_count, max_mem_recs)


    def _specs_cleaner(self,
                       specs: List[str],
                       header: Optional[csvhelper.Header],
                       infile_item_count: int) -> List[Tuple[str, str]]:
        """ Returns a transformed version of the specs

        Args:
            Specs: these are raw specs, ex: [':5', ':', '4', '3:19']
            header: this is a csv header object - used to translate names to numbers
            infile_item_count: this is either a row count or a column count, depending
              on whether the class is used for rows or cols
        Returns:
            clean_specs: ex: [[None, 5], [None, None], [4], [3, 19]]
        """

        def transform_none(val: str) -> str:
            return None if val.strip() == '' else val

        def transform_number(val: str) -> str:
            if comm.isnumeric(part):
                number = int(val)
                return number
            else:
                return val

        def transform_name(val: str) -> str:
            if val is None:
                return val
            if comm.isnumeric(val):
                return val
            try:
                position = str(header.get_field_position(val))
            except KeyError:
                comm.abort(f'Error: Invalid string in spec: {part}',
                           f'Not in header list: {header.field_names}')
            return position

        def transform_negative_number(val: str) -> str:
            if val is not None and int(val) < 0:
                return str(infile_item_count + int(val) + 1 )
            else:
                return val

        def validate_spec(spec: List[str]) -> None:
            if len(spec) > 2:
                raise ValueError(f'spec has too many parts: {spec}')
            if len(spec) == 2 and spec[0] and spec[1]:
                if int(spec[0]) >= int(spec[1]):
                    raise ValueError(f'spec is an invalid range: {spec}')

        clean_specs = []
        for item in specs:
            new_parts = []
            for part in item.split(':'):
                part = part.strip()
                part = transform_none(part)
                part = transform_number(part)
                part = transform_name(part)
                part = transform_negative_number(part)
                new_parts.append(int(part) if part is not None else None)
            validate_spec(new_parts)
            clean_specs.append(new_parts)
        return clean_specs


    def _specs_range_expander(self,
                              infile_item_count: int,
                              max_mem_recs: int) -> Optional[List[int]]:
        """ Explodes the specification ranges into individual positions.

        This function returns a list of all positions that are included within a
        specification - whether they're directly references, or they fall within
        a range.

        Note that if the number of elements of the resulting list exceeds the
        max_mem_recs then this function will return None.

        Args:
            infile_item_count: the number of rows in the file or cols in the row.
            max_mem_recs: the maximum number of records to explode a specification
            into.  If this is exceeded then return None.
        """

        expanded_spec = []
        for parts in self.clean_specs:
            if len(parts) == 1:
                expanded_spec.append(int(parts[0]))
            elif len(parts) == 2:
                start_part = 0 if parts[0] is None else int(parts[0])
                stop_part = infile_item_count+1 if parts[1] is None else int(parts[1])
                for part in range(start_part, stop_part):
                    expanded_spec.append(int(part))
            if len(expanded_spec) > max_mem_recs:
                sys.stderr.write('WARNING: insufficient memory - may be slow\n')
                return None
        return expanded_spec


    def specs_evaluator(self,
                        location: int) -> bool:
        """ Evaluates a location (column number or record number) against
        a specifications list.  Description:
            - uses the python string slicing formats to specify valid ranges
            (all offset from 0):
            - [4]      = location 4
            - [1,3]    = location 1 & 2 (end - 1)
            - [5,None] = location 5 to the end
            - [None,5] = location 0 to 4 (end - 1)
            - [None,None] = all locations
            - template:  spec, spec, spec:spec, spec, spec:spec
            - example:   [4] , [8] , [10,14]  , [21], [48,55]
            - The above example is stored in a five-element spec-list
        Args:
            - location:  a column or record number
        Returns:
            - True if the number matches one of the specs
            - False if the number does not match one of the specs
            - False if the spec_list is empty
        """
        if any([self._spec_item_check(spec, location) for spec in self.clean_specs]):
            return True
        return False


    def _spec_item_check(self,
                         spec: str,
                         location: int) -> bool:
        """ evaluates a single item against a location
        Args:
            - spec: one line of the specifications, looking like:
                - [5]
                - [1, 10]
                - [None, 10]
                - [1, None]
                - [None, None]
            - location - an integer to be compared to spec
        Returns:
            - True or False
        """
        if len(spec) == 1:
            if spec[0] == location:
                return True
            else:
                return False
        else:
            if spec == [None, None]:  # unbounded on both sides
                return True
            elif spec[1] is None and location >= spec[0]:  # unbounded on right
                return True
            elif spec[0] is None and location < spec[1]:   # unbounded on left
                return True
            elif (spec[0] is not None and location >= spec[0]   # within range
                    and spec[1] is not None and location < spec[1]):
                return True
            else:
                return False



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




