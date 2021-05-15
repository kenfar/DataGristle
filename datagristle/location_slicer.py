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

from pprint import pprint as pp
import re
import sys
from typing import List, Dict, Tuple, Union, Any, Optional

import datagristle.common as comm
import datagristle.csvhelper as csvhelper



def is_sequence(val: Any) -> bool:
    """ test whether or not val is a squence - list or tuple
            input:  val
            output:  True or False
    """
    if isinstance(val, (list, tuple)):
        return True
    else:
        return False



class SpecProcessor(object):

    def __init__(self,
                 spec: List[str],
                 spec_name: str,
                 header: csvhelper.Header = None) -> None:
        """
        Header: Is always expected for column specs that read from files, but will just be None
                for columns specs for stdin inputs.  Is also always None for record specs.
        """

        self.spec_name = spec_name
        self.numeric_spec: List[Optional[str]] = None # spec with names converted to positions
        self.adj_spec: List[Optional[str]] = None  # spec with negatives converted

        if header is not None:
            self.numeric_spec = self._spec_name_translater(spec, header)
        else:
            self.numeric_spec = spec

        self._spec_validator(self.numeric_spec)      # will raise exceptions if any exist


    def has_negatives(self) -> bool:
        """ Checks for negative values in a single spec lists.
            Each string within the list will be searched for a '-' sign.
        """
        for item in self.numeric_spec:
            if '-' in item:
                return True
        return False


    def _spec_name_translater(self,
                              spec: List[str],
                              header: csvhelper.Header) -> List[str]:
        """ Reads through a single spec (ie, record inclusion spec, column
            exclusion spec, etc) and remaps any column names to their position
            offsets.
            Inputs:
                - spec, ex: [' 1',' -3',' 4:7', ' home_state', ' last_name:']
                - header object
            Outputs:
                - a numeric-only spec, ex: ['1','-3','4:7','9','12:']
        """
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
        if not is_sequence(spec):
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


    def spec_adjuster(self, loc_max: Optional[int]=None) -> None:
        """ Reads through a single spec (ie, record inclusion spec, column
            exclusion spec, etc) and remaps any negative values to their positive
            equiv.
            Inputs:
                - the max number of items to apply the spec to.  The location
                  starts at an offset of 0.  So, a 4-item list will have a
                  max-loc of 3.
            Outputs:
                - none
        """
        if loc_max is None:
            if self.has_negatives():
                raise ValueError('adjust_specs missing loc_max - and has negative specs')

        adj_spec: List[Optional[str]] = []
        for item in self.numeric_spec:
            parts = item.split(':')
            new_parts = []
            for part in parts:
                if part is None or part == '':
                    new_parts.append(part)
                else:
                    if int(part) < 0:
                        new_parts.append(str(loc_max + int(part) + 1 ))
                    else:
                        new_parts.append(part)
            adj_spec.append(':'.join(new_parts))
        self.adj_spec = adj_spec


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
        if not self.adj_spec:
            # the self.adj_spec will often be None for 1-2 of the 4 specs.
            # ex: incl criteria provided (or defaulted to ':'), but if no
            # excl critieria provided it will be None.
            return False

        if any([self._spec_item_evaluator(x, int(location)) for x in self.adj_spec]):
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
