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
import functools
import more_itertools
from pprint import pprint as pp
import re
import random
import sys
from typing import List, Dict, Tuple, Union, Any, Optional

from pydantic.dataclasses import dataclass
from pydantic import BaseModel, ValidationError, validator, root_validator

import datagristle.common as comm
import datagristle.csvhelper as csvhelper


START = 0
STOP = 1
STEP = 2

class SpecProcessor:
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
        self.specs = specs

        self.has_exclusions = specs.has_exclusions()
        self.has_all_inclusions = specs.has_all_inclusions()

        self.indexer = Indexer(self.specs.specs_final,
                               self.specs.max_items)
        self.indexer.builder()
        self.index = self.indexer.index



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
        # Note that the has_all_inclusions optimization will automatically approve all
        # locations - so this depends on the calling code to only give valid locations (ex,
        # those within the range of the file.
        if self.has_all_inclusions:
            return True

        if any([self._spec_item_check(spec, location) for spec in self.specs.specs_final]):
            return True
        return False


    def _spec_item_check(self,
                         spec: List[Optional[int]],
                         location: int) -> bool:
        """ evaluates a single item against a location
        Args:
            - spec: one line of the specifications, looking like:
                - [5, 5, 1]
                - [1, 10, 1]
                - [3, 10, 2]
                - [2, 0, -1]
                - [1, 3, 0.25]
            - location - an integer to be compared to spec
        Returns:
            - True or False
        """
        if location >= spec.start and location < spec.stop:

            if 0 < spec.step < 1:
                rec_num = location - spec.start
                r = random.random()
                if abs(spec.step) > r:
                    return True
            else:
                if (location - spec.start) % spec.step == 0:
                    return True

        return False


class SpecRecord(BaseModel):
    start:      int
    stop:       int
    step:       float

    @validator('step')
    def step_must_be_nonzero(cls, val) -> float:
        if val == 0:
            comm.abort('step must be non-zero')
        return val

    @validator('step')
    def step_precision(cls, val) -> float:
        if val < 0 or val >= 1:
            if val != int(val):
                comm.abort('steps less than zero or greater than 1 cannot have decimal precision')
        return val

    @root_validator()
    def start_stop_relationship(cls, values: Dict) -> Dict:
        start = values.get('start')
        stop = values.get('stop')
        step = values.get('step')
        if step > 0:
            if start > stop:
                comm.abort(f'spec has start ({start}) after stop ({stop})')
        if step < 0:
            if start < stop:
                comm.abort(f'negative spec has start ({start}) before stop ({stop})',
                           'negative specs require the start (start:stop:step) to be AFTER the stop')
        return values



class Specifications:

    def __init__(self,
                 spec_type: str,
                 specs_strings: List[str],
                 header: Optional[csvhelper.Header] = None,
                 infile_item_count: Optional[int] = -1,   #### actually max value!
                 max_items: int=sys.maxsize):

        self.spec_type = spec_type
        self.specs_strings = specs_strings
        self.header = header
        self.infile_item_count = infile_item_count
        self.max_items = max_items

        assert spec_type in ['incl_rec', 'excl_rec', 'incl_col', 'excl_col']

        self.specs_final: List[SpecRecord] = self.specs_cleaner()


    def specs_cleaner(self) -> List[Optional[List[Optional[int]]]]:
        """ Returns a transformed version of the specs

        Args:
            Specs: these are raw specs, ex: [':5', ':', '4', '3:19']
            header: this is a csv header object - used to translate names to numbers
            infile_item_count: this is either a row max or a column max, depending
              on whether the class is used for rows or cols.  May be None if there are
              no negatives or unbounded ranges in the specs.
        Returns:
            clean_specs: ex: [[None, 5], [None, None], [4, 4], [3, 19]]
            for specs that are empty   (ex: '') returns: []
            for specs that are default (ex: ':') returns: [[0, None]]
            NOTE: the end of the rang eis inclusive, not exclusive
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
                if self.infile_item_count == -1:
                    raise NegativeOffsetWithoutItemCountError
                return str(self.infile_item_count + int(val) + 1)
            else:
                return val

        def transform_to_triples(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Ensures that even a single col spec gets turned into a range: [val, val+1]
            if len(spec) == 1:
                return [spec[START], spec[START]+1, 1]
            elif len(spec) == 2:
                return [spec[START], spec[STOP], 1]
            elif len(spec) == 3 and spec[2] is None:
                return [spec[START], spec[STOP], 1]
            else:
                return spec

        def transform_none_start(spec: List[Optional[int]]) -> List[Optional[int]]:
            # Transform none start to zero
            if spec[STEP] >= 0:
                if spec[START] is None:
                    spec[START] = 0
            else:
                if spec[START] is None:
                    if self.infile_item_count == -1:
                        raise NegativeStepWithoutItemCountError
                    else:
                        spec[START] = self.infile_item_count
            return spec

        def transform_none_stop(spec: List[Optional[int]]) -> List[Optional[int]]:
            # if step is provided, stop is unbounded, set stop to count+1
            if spec[STOP] in (None, ''):
                if spec[STEP] >= 0:
                    if self.infile_item_count > -1:
                        spec[STOP] = self.infile_item_count + 1
                    else:
                        spec[STOP] = self.max_items
                else:
                    spec[STOP] = -1
            return spec

        def pre_validate_spec_structure(spec: List[Optional[int]]) -> None:
            if len(spec) == 0:
                comm.abort(f'spec is empty')
            if len(spec) == 1:
                comm.abort(f'spec is only has a single value')


        if len(self.specs_strings) == 1:
            if self.specs_strings[0].strip() == '':
                self.specs_strings[0] = ':'

        final_specs = []
        for item in self.specs_strings:
            new_parts = []
            if item.count(':') > 2:
                comm.abort(f'spec has too many parts: {item}')

            for i, part in enumerate(item.split(':')):

                orig_opt_part: Optional[str] = part.strip()

                opt_part = transform_none(orig_opt_part)

                if i in (START, STOP):
                    opt_part = transform_name(opt_part)
                    opt_part = transform_negative_number(opt_part)

                if len(part) > 0 and not comm.isnumeric(opt_part):
                    comm.abort(f'Invalid spec has item ({item}) with a non-numeric part: {opt_part}')

                if i in (START, STOP):
                    new_parts.append(int(opt_part) if opt_part is not None else None)

                if i in (STEP,):
                    if opt_part is not None and '.' in opt_part:
                        new_parts.append(float(opt_part) if opt_part is not None else None)
                    else:
                        new_parts.append(int(opt_part) if opt_part is not None else None)

            triples = transform_to_triples(new_parts)
            triples = transform_none_start(triples)
            triples = transform_none_stop(triples)
            pre_validate_spec_structure(triples)
            try:
                final_rec = SpecRecord(start=triples[0], stop=triples[1], step=triples[2])
            except ValidationError as err:
                comm.abort('Error: invalid specification',  f'{triples[0]}:{triples[1]}:{triples[2]}')
            final_specs.append(final_rec)
        return final_specs


    def has_everything(self) -> bool:
        assert self.specs_strings != []
        return self.specs_strings == [':']


    def has_all_inclusions(self) -> bool:
        return self.spec_type in ('incl_col', 'incl_rec') and self.specs_strings == [':']


    def has_exclusions(self) -> bool:
        return self.spec_type in ('excl_col', 'excl_rec') and self.specs_final != []




class Indexer:

    def __init__(self,
                 specs,
                 max_items) -> List[int]:

        self.specs = specs
        self.max_items = max_items
        self.index = []
        self.valid = False


    def builder(self):
        """ Explodes the specification ranges into individual positions.

        This function returns a list of all positions that are included within a
        specification - whether they're directly references, or they fall within
        a range.

        Args:
            infile_item_count: the number of rows in the file or cols in the row.
                This value may be -1 if the calling pgm doesn't think we need to
                know what the last record is.
        """
        max_items = self.max_items
        specs = self.specs # lets make this a local ref for speed
        index = []
        count = 0

        for rec in specs:

            start_part = rec.start
            stop_part = rec.stop
            step_part = rec.step

            if step_part == int(step_part):  # consistent interval steps
                if stop_part == max_items:
                    return  # quit & leave valid=False
                for part in range(start_part, stop_part, int(step_part)):
                    count += 1
                    if count > max_items:
                        return  # quit & leave valid=False
                    index.append(part)
            elif step_part < 1.0:           # random interval steps
                multiplier = 1 if step_part > 0 else -1
                for part in range(start_part, stop_part, 1*multiplier):
                    result =  random.random()
                    if abs(step_part) > result:
                        count += 1
                        if count > max_items:
                            return  # quit & leave valid=False
                        index.append(part)
            else:
                 comm.abort('Error! Invalid specification step',
                            f'step: {step_part} is invalid')
        else:
            self.valid = True

        self.index = index


    def has_repeats(self) -> bool:
        # Lets assume that there may be repeats if the index build failed:
        if not self.valid:
            return False

        # Only works if specs_expanded has been populated!
        if len(set(self.index)) != len(self.index):
            return True

        return False




def is_out_of_order(index) -> bool:
    """
    Considers either mixed-order or reverse order True
    """
    last_val = None
    for val in index:
        if last_val is None:
            last_val = val
        elif val < last_val:
            return True
        elif val == last_val:
            continue
        else:
            last_val = val
    return False




def spec_has_negatives(spec: List[str]) -> bool:
    """ Checks for negative values in a list of specs
    """
    for item in spec:
        parts = item.split(':')
        for i, part in enumerate(parts):
            if i in (0,1):
                if comm.isnumeric(part):
                    if int(part) < 0:
                        return True
    return False



def spec_has_unbounded_end(spec: List[str]) -> bool:
    """ Checks for unbounded outer range in a list of specs

        Does not consider that the first part of a single spec
        is the stopping offset when using negative steps.
    """
    if spec in ([], [':'], ['::']):
        return True
    for item in spec:
        parts = item.split(':')
        if len(parts) in (2, 3):
            if parts[1] == '':
                return True
        elif len(parts) == 1:
            if parts[0].strip() == '':
                return True
    return False



#def get_size(obj, seen=None):
#    """Recursively finds size of objects"""
#    size = sys.getsizeof(obj)
#    if seen is None:
#        seen = set()
#    obj_id = id(obj)
#    if obj_id in seen:
#        return 0
#    # Important mark as seen *before* entering recursion to gracefully handle
#    # self-referential objects
#    seen.add(obj_id)
#    if isinstance(obj, dict):
#        size += sum([get_size(v, seen) for v in obj.values()])
#        size += sum([get_size(k, seen) for k in obj.keys()])
#    elif hasattr(obj, '__dict__'):
#        size += get_size(obj.__dict__, seen)
#    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
#        size += sum([get_size(i, seen) for i in obj])
#    return size
#


class ItemCountTooBigException(Exception):
    pass

class NegativeOffsetWithoutItemCountError(Exception):
    pass

class NegativeStepWithoutItemCountError(Exception):
    pass
