#!/usr/bin/env python
""" Applies a list of python slicing specifications to a number to determine if
    that number meets the specifications or not.

    Typical Usage:
        >>> sp = location_slicer.SpecProcessor(raw_specs=['1','5','10:20','70:-1'],
        >>>                                    header=None,
        >>>                                    infile_item_count=80)
        >>> sp.specs_evaluator(5)
        True
        >>> sp.specs_evaluator(0)
        False
        >>> sp.specs_evaluator(15)
        True
        >>> sp.specs_evaluator(78)
        True
        >>> sp.specs_evaluator(79)
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

import functools
import more_itertools

import datagristle.common as comm
import datagristle.csvhelper as csvhelper

ALL_COLS = 9876543210987654321


class SpecProcessor(object):
    """ Manages all types of specifications - inclusion or exclusion for rows & cols.

    That means, it translates the specs into useful structures, and supports the
    evaluation of col or row numbers aginst the specs.
    """

    def __init__(self,
                 raw_specs: List[str],
                 name: Optional[str],
                 header: Optional[csvhelper.Header],
                 infile_item_count: Optional[int]) -> None:
        """
        Header: Is always expected for column specs that read from files, but will just be None
                for columns specs for stdin inputs.  Is also always None for record specs.
        """
        self.name = name

        self.clean_specs: List[List[Optional[int]]] \
            = self._specs_cleaner(raw_specs, header, infile_item_count)

        try:
            self.expanded_specs: List[int] \
                = self._specs_range_expander(infile_item_count)
            self.expanded_specs_valid = True
        except ItemCountException as err:
            self.expanded_specs = []
            self.expanded_specs_valid = False


    def specs_are_out_of_order(self) -> bool:
        last_spec = [None, None]
        for spec in self.clean_specs:
            if last_spec[0] is not None and spec[0] is None:
                last_spec = spec
                return True
            if (last_spec[0] is not None and spec[0] is not None
                    and last_spec[0] > spec[0]):
                last_spec = spec
                return True
            last_spec = spec
            #todo: what if they're both none? ie, 2 nones in a row?
        return False

    def specs_have_unbounded_ends(self) -> bool:
        x = [x[1] for x in self.clean_specs if x[1] is None]
        if len(x) > 0:
            return True
        else:
            return False

    def specs_have_negatives(self) -> bool:
        flat_specs = more_itertools.collapse(self.clean_specs)
        flat_specs = [x for x in flat_specs if x is not None and x < 0]
        if len(flat_specs) > 0:
            return True
        else:
            return False


    def _specs_cleaner(self,
                       specs: List[str],
                       header: Optional[csvhelper.Header],
                       infile_item_count: Optional[int]) -> List[Optional[List[Optional[int]]]]:
        """ Returns a transformed version of the specs

        Args:
            Specs: these are raw specs, ex: [':5', ':', '4', '3:19']
            header: this is a csv header object - used to translate names to numbers
            infile_item_count: this is either a row count or a column count, depending
              on whether the class is used for rows or cols.  May be None if there are
              no negatives or unbounded ranges in the specs.
        Returns:
            clean_specs: ex: [[None, 5], [None, None], [4, 4], [3, 19]]
            for specs that are empty   (ex: '') returns: []
            for specs that are default (ex: ':') returns: [[0, None]]
        """
        def transform_none(val: Optional[str]) -> Optional[str]:
            if val is None:
                return None
            elif val.strip() == '':
                return None
            else:
                return val

        def transform_name(val: Optional[str]) -> Optional[str]:
            if val is None:
                return None
            if comm.isnumeric(val):
                return val
            if header is None:
                comm.abort(f'Error: non-numeric specs without a header to translate')
            try:
                position = str(header.get_field_position(val))
            except KeyError:
                comm.abort(f'Error: Invalid string in spec: {part}',
                           f'Not in header list: {header.field_names}')
            return position

        def transform_negative_number(val: Optional[str]) -> Optional[str]:
            if val is not None and int(val) < 0:
                assert infile_item_count > -1
                return str(infile_item_count + int(val) + 1 )
            else:
                return val

        def transform_singles(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Ensures that even a single col spec gets turned into a range: [val, val+1]
            if len(spec) == 1:
                return [spec[0], spec[0]+1]
            else:
                return spec

        def transform_none_start(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Transform none start to zero
            if spec[0] is None:
                spec[0] = 0
            return spec

        def transform_none_stop(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Transform none start to zero
            if self.name in ('incl_col_slicer', 'excl_col_slicer') and spec[1] is None:
                spec[1] = ALL_COLS
            return spec

        def validate_spec(spec: List[Optional[int]]) -> None:
            if len(spec) == 0:
                raise ValueError(f'spec is empty')
            if len(spec) == 1:
                raise ValueError(f'spec is only has a single value')
            if len(spec) > 2:
                raise ValueError(f'spec has too many parts: {spec}')
            if len(spec) == 2 and spec[0] and spec[1]:
                if spec[0] >= spec[1]:   # type: ignore
                    raise ValueError(f'spec is an invalid range: {spec}')

        clean_specs = []
        for item in specs:
            new_parts = []
            for part in item.split(':'):
                opt_part: Optional[str] = part.strip()
                opt_part = transform_none(opt_part)
                opt_part = transform_name(opt_part)
                opt_part = transform_negative_number(opt_part)
                new_parts.append(int(opt_part) if opt_part is not None else None)
            doubles = transform_singles(new_parts)
            doubles = transform_none_start(doubles)
            doubles = transform_none_stop(doubles)
            validate_spec(doubles)
            clean_specs.append(doubles)
        return clean_specs


    def _specs_range_expander(self,
                              infile_item_count: Optional[int]) -> List[int]:
        """ Explodes the specification ranges into individual positions.

        This function returns a list of all positions that are included within a
        specification - whether they're directly references, or they fall within
        a range.

        Args:
            infile_item_count: the number of rows in the file or cols in the row.
                This value may be -1 if the calling pgm doesn't think we need to
                know what the last record is.
        """
        expanded_spec = []
        START = 0
        STOP  = 1
        for parts in self.clean_specs:

            assert len(parts) == 2

            if parts[START] is None:
                start_part = 0
            else:
                start_part = parts[START]

            if parts[STOP] is None:
                if infile_item_count == -1:
                    raise ItemCountException('infile_item_count is negative')
                stop_part = infile_item_count + 1
            else:
                stop_part = parts[STOP]

            for part in range(start_part, stop_part):
                if self.name in ('incl_col_slicer', 'excl_col_slicer') and stop_part == ALL_COLS:
                    return [] # it's derrived value that stands for "everything" 
                expanded_spec.append(part)

        return expanded_spec


    @functools.cache
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
                         spec: List[Optional[int]],
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
            elif spec[1] is None and location >= spec[0]:  # type: ignore
                return True
            elif spec[0] is None and location < spec[1]:   # type: ignore
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

def spec_has_unbounded_end_range(spec: List[str]) -> bool:
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




class ItemCountException(Exception):
    pass
