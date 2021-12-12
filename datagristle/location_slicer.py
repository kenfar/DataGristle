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
import random

import datagristle.common as comm
import datagristle.csvhelper as csvhelper

#ALL_ITEMS = 9876543210987654321


class SpecProcessor(object):
    """ Manages all types of specifications - inclusion or exclusion for rows & cols.

    That means, it translates the specs into useful structures, and supports the
    evaluation of col or row numbers aginst the specs.
    """

    def __init__(self,
                 specs) -> None:
        """
        Header: Is always expected for column specs that read from files, but will just be None
                for columns specs for stdin inputs.  Is also always None for record specs.
        """
        self.all_items = False
        self.specs = specs
        self.expanded_specs = []
        self.expanded_specs_valid = False

        #pp(f'{self.specs.spec_type=}')
        if specs.get_all_items():
            #pp(f'ALL_ITEMS ASSIGNED!!!!!!!!!!!!!!!!!')
            self.all_items = True
        else:
            try:
                self.expanded_specs: List[int] \
                    = self.specs.specs_range_expander()
                self.expanded_specs_valid = True
            except ItemCountException as err:
                self.expanded_specs = []
                self.expanded_specs_valid = False
        #pp(f'{self.expanded_specs_valid=}')



   #### @functools.cache
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
        if self.all_items:
            #pp('cccccccccccccccccccccccccccc')
            return True
        elif any([self._spec_item_check(spec, location) for spec in self.specs.specs_cleaned]):
            #pp('dddddddddddddddddddddddddddd')
            return True
        #pp('eeeeeeeeeeeeeeeeeeeeeeee')
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
        assert len(spec) == 3
        assert spec[0] is not None
        assert spec[1] is not None
        assert spec[2] is not None

        if location >= spec[0] and location < spec[1]:
            if (location - spec[0]) % spec[2] == 0:
                return True

        return False

#todo: add validation for step != 0
#todo: add validation for step positive if start > stop, negative otherwise


class Specifications:

    def __init__(self,
                 spec_type: str,
                 specs_strings: List[str],
                 header: Optional[csvhelper.Header] = None,
                 infile_item_count: Optional[int] = -1):

        self.spec_type = spec_type
        self.specs_strings = specs_strings
        self.header = header
        self.infile_item_count = infile_item_count
        self.specs_cleaned = self._specs_cleaner()
        self.reverse_order_with_neg_stop = False


    def _specs_cleaner(self) -> List[Optional[List[Optional[int]]]]:
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
            if self.header is None:
                comm.abort(f'Error: non-numeric specs without a header to translate')
            try:
                position = str(self.header.get_field_position(val))
            except KeyError:
                comm.abort(f'Error: Invalid string in spec: {part}',
                           f'Not in header list: {self.header.field_names}')
            return position

        def transform_negative_number(val: Optional[str]) -> Optional[str]:
            if val is not None and int(val) < 0:
                #assert self.infile_item_count > -1
                if self.infile_item_count == -1:
                    return val
                return str(self.infile_item_count + int(val) + 1 )
            else:
                return val

        def transform_to_triples(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Ensures that even a single col spec gets turned into a range: [val, val+1]
            if len(spec) == 1:
                return [spec[0], spec[0]+1, 1]
            elif len(spec) == 2:
                return [spec[0], spec[1], 1]
            elif len(spec) == 3 and spec[2] is None:
                return [spec[0], spec[1], 1]
            else:
                return spec

        def transform_none_start(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Transform none start to zero
            if spec[2] >= 0:
                if spec[0] is None:
                    spec[0] = 0
            else:
                if spec[0] is None:
                    spec[0] = self.infile_item_count
            return spec

        def transform_none_stop(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Transform none start to zero
            #if self.name in ('incl_col_slicer') and spec[1] is None:
            #    spec[1] = ALL_ITEMS
            if spec[2] >= 0:
                if spec[1] in (None, ''):
                    spec[1] = self.infile_item_count + 1
            else:
                if spec[1] in (None, ''):
                    spec[1] = 0
            return spec

        def validate_spec(spec: List[Optional[int]]) -> None:
            if len(spec) == 0:
                raise ValueError(f'spec is empty')
            if len(spec) == 1:
                raise ValueError(f'spec is only has a single value')
            if len(spec) > 3:
                raise ValueError(f'spec has too many parts: {spec}')
            if len(spec) == 2 and spec[0] and spec[1]:
                if spec[0] >= spec[1]:   # type: ignore
                    raise ValueError(f'spec is an invalid range: {spec}')

        clean_specs = []

        if len(self.specs_strings) == 1:
            if self.specs_strings[0].strip() == '':
                self.specs_strings[0] = ':'

        for item in self.specs_strings:
            new_parts = []
            #pp(f'cleaner: {self.spec_type}.{item}')
            for i, part in enumerate(item.split(':')):
                orig_opt_part: Optional[str] = part.strip()
                #pp(f'orig_opt_part: {orig_opt_part}')
                opt_part = transform_none(orig_opt_part)
                #pp(f'transform_none: {opt_part}')
                if i in (0, 1):
                    opt_part = transform_name(opt_part)
                #pp(f'transform_name: {opt_part}')
                if i in (0, 1):
                    opt_part = transform_negative_number(opt_part)
                #pp(f'transform_neg: {opt_part}')
                if i in (0, 1):
                    new_parts.append(int(opt_part) if opt_part is not None else None)
                elif '.' in opt_part:
                    new_parts.append(float(opt_part) if opt_part is not None else None)
                else:
                    new_parts.append(int(opt_part) if opt_part is not None else None)

            #pp(f'{new_parts=}')
            triples = transform_to_triples(new_parts)
            #pp(f'triples: {triples}')
            triples = transform_none_start(triples)
            #pp(f'transform_none_start: {triples}')
            triples = transform_none_stop(triples)
            #pp(f'transform_none_stop: {triples}')
            validate_spec(triples)
            clean_specs.append(triples)
            #pp(f'{clean_specs=}')
        return clean_specs


    def specs_range_expander(self) -> List[int]:
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
        STEP  = 2
        #pp('-------------- _specs_range_expander: ----------------')
        #pp(f'{self.name=}')
        #pp(f'{self.clean_specs=}')
        #if self.name in ('incl_col_slicer') and self.clean_specs == [[0, ALL_ITEMS]]:
        #    return []

        #if self.spec_type == 'incl_rec':
            #pp('===========================================')
            #pp(f'expander: {self.spec_type=}')
            #pp(f'expander: {self.specs_cleaned=}')
            #pp('===========================================')

        for parts in self.specs_cleaned:

            assert len(parts) == 3
            assert parts[START] is not None
            assert parts[STOP] is not None
            assert parts[STEP] is not None

            start_part = parts[START]
            stop_part = parts[STOP]
            step_part = parts[STEP]
            #pp(f'------------- {start_part=}.{stop_part=}.{step_part=} ---------------')

            if self.specs_have_reverse_order():
                adjusted_stop_part = stop_part
            else:
                adjusted_stop_part = stop_part

            if type(step_part) == type(5):
                for part in range(start_part, adjusted_stop_part, step_part):
                    #pp(f'part: {part}')
                    #if self.name in ('incl_col_slicer') and stop_part == ALL_ITEMS:
                    #    return [] # it's derrived value that stands for "everything" 
                    expanded_spec.append(part)
            else:
                #pp('aaaaaaaaaaaaaaaaaaa')
                multiplier = 1 if step_part > 0 else -1
                for part in range(start_part, adjusted_stop_part, 1*multiplier):
                    result =  random.random()
                    #pp(step_part)
                    #pp(result)
                    if abs(step_part) > result:
                        #pp(f' {step_part=} > {result=}')
                        expanded_spec.append(part)

        #pp(f'{expanded_spec=}')
        #pp(get_size(expanded_spec))
        return expanded_spec

        # todo: resolve tricky problem with ranges:
        #   1. The stop number is 1 more than the actual number included
        #   2. The stop number is 1 less for negatives
        #   3. To go in reverse order down to 0 you have to stop at -1
        #   4. But -1 is translated to the end record of the file!



    def specs_are_out_of_order(self) -> bool:
        last_spec = [None, None, None]
        for spec in self.specs_cleaned:

            # combining none with actual positions for starts
            if last_spec[0] is not None and spec[0] is None:
                last_spec = spec
                return True

            # starts deminish in value:
            if (last_spec[0] is not None and spec[0] is not None
                    and last_spec[0] > spec[0]):
                last_spec = spec
                return True

            # negative steps - or reverse sort:
            if spec[2] < 0:
                return True

            last_spec = spec
            #todo: what if they're both none? ie, 2 nones in a row?
        return False


    def specs_have_unbounded_ends(self) -> bool:
        x = [x[1] for x in self.specs_cleaned if x[1] is None]
        if len(x) > 0:
            return True
        else:
            return False


# todo: test this - not sure how it works with 3+ elements
    def specs_have_negatives(self) -> bool:
        flat_specs = more_itertools.collapse(self.specs_cleaned)
        flat_specs = [x for x in flat_specs if x is not None and x < 0]
        if len(flat_specs) > 0:
            return True
        else:
            return False


    def specs_have_reverse_order(self) -> bool:
        for spec in self.specs_cleaned:
            if spec[2] < 0:
                return True
        return False


    def specs_are_for_everything(self) -> bool:
        return self.specs_strings == [':']


    def get_all_items(self) -> bool:
        #pp('===============================================')
        #pp(self.spec_type)
        #pp(self.specs_strings)
        #pp('===============================================')
        return self.spec_type in ('incl_col', 'incl_rec') and self.specs_strings == [':']



def spec_recs_are_default(rec_spec: List[str],
                          exrec_spec: List[str]) -> bool:
    """
    """
    if rec_spec == [':'] and exrec_spec == []:
        return True
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
    #pp('==========================================')
    #pp(spec)
    #pp('==========================================')
    if spec in ([], [':'], ['::']):
        return True
    for item in spec:
        parts = item.split(':')
        if len(parts) == 2:
            if parts[1] == '':
                return True
        elif len(parts) == 1:
            if parts[0].strip() == '':
                return True
    return False


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size



class ItemCountException(Exception):
    pass
