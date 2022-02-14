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

MAX_INDEX_REC_CNT = 1_000_001


START = 0
STOP = 1
STEP = 2


class SpecRecord(BaseModel):
    start:      int
    stop:       int
    step:       float
    spec_type:  str

    @validator('step')
    def step_must_be_nonzero(cls, val) -> float:
        if val == 0:
            comm.abort('step must be non-zero')
        return val

    @root_validator()
    def start_stop_relationship(cls, values: Dict) -> Dict:
        start = values['start']
        stop = values['stop']
        step = values['step']
        if step > 0:
            if start > stop:
                comm.abort(f'spec has start ({start}) after stop ({stop})')
        if step < 0:
            if start < stop:
                comm.abort(f'negative spec has start ({start}) before stop ({stop})',
                           'negative specs require the start (start:stop:step) to be AFTER the stop')
        return values

    @root_validator()
    def limit_offsets_to_inclusions(cls, values: Dict) -> Dict:
        spec_type = values.get('spec_type')
        step = values.get('step')
        if spec_type not in ('incl_rec', 'incl_col'):
            if step != 1.0:
                comm.abort(f'Error: exclusion spec is not allowed to have steps: {step}')
        return values

    def is_full_step(self):
        if self.step == int(self.step):
            return True
        return False

    def is_negative_step(self):
        if self.step < 0:
            return True
        return False

    def is_random_step(self):
        if -1 < self.step < 1:
            return True
        return False

    def is_sysmaxsize_stop(self):
        if self.stop == sys.maxsize:
            return True
        return False







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

        self.indexer = Indexer(self.specs.specs_final)
        self.indexer.builder()
        self.index = self.indexer.index

        # out of order: will include any reverse-order specs:
        self.includes_out_of_order = self.indexer.includes_out_of_order
        # repeats won't catch out of order repeats
        self.includes_repeats = self.indexer.includes_repeats
        self.includes_reverse = self.indexer.includes_reverse



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
                         spec: type[SpecRecord],
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



class Specifications:

    def __init__(self,
                 spec_type: str,
                 specs_strings: List[str],
                 header: Optional[csvhelper.Header] = None,
                 infile_item_count: int = None,
                 item_max: int=sys.maxsize):

        self.spec_type = spec_type
        self.specs_strings = specs_strings
        self.header = header
        self.infile_item_count = infile_item_count
        self.item_max = item_max

        assert spec_type in ['incl_rec', 'excl_rec', 'incl_col', 'excl_col']

        self.specs_final: List[SpecRecord] = self.specs_cleaner()


    def specs_cleaner(self) -> List[SpecRecord]:
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

        Example inputs:
            - [':']
            - ['::']
            - ['3']
            - ['-3']
            - ['3', '1']
            - ['::']
            - ['::-1']
            - ['3::-1']
            - [':9:-1']
            - ['2:9:-1']
            - ['2:9:2']
            - ['2:9:0.5']
            - ['account:customer']
        Weird Example inputs:
            - [':', '1']
        """


        if len(self.specs_strings) == 1:
            if self.specs_strings[0].strip() == '':
                self.specs_strings[0] = ':'

        final_specs = []
        for item in self.specs_strings:

            try:
                #pp('')
                start, stop, step, is_range = self.phase_one__item_parsing(item)
                #pp(f'phase one results: {start}, {stop}, {step}, {is_range}')

                int_start, int_stop, float_step = self.phase_two__translate_item_parts(start, stop, step, is_range)
                #pp(f'phase two results: {int_start}, {int_stop}, {float_step}, {is_range}')

                int_start, int_stop, float_step = self.phase_three__resolve_dependencies(int_start, int_stop, float_step, is_range)
                #pp(f'phase three results: {int_start}, {int_stop}, {float_step}, {is_range}')
                try:
                    final_rec = SpecRecord(start=int_start, stop=int_stop, step=float_step, spec_type=self.spec_type)
                except ValidationError as err:
                    comm.abort('Error: invalid specification',  f'{self.spec_type}: {start}:{stop}:{step}')
                final_specs.append(final_rec)
            except OutOfRangeError:
                # fixme: confirm that we still want to do this!
                # Just drop & ignore OutOfRangeError
                continue
        return final_specs


    def phase_one__item_parsing(self, item: str) -> Tuple[Optional[str], Optional[str], str, bool]:
        """ Split a specification item string into separate parts
        """
        parts = item.split(':')
        if len(parts) > 3:
            comm.abort(f'Error: spec item has too many parts: {item}')

        is_range = True if len(parts) > 1 else False

        start = parts[0]
        stop = parts[1] if len(parts) > 1 else None
        step = parts[2] if len(parts) > 2 else '1'

        return start, stop, step, is_range


    def phase_two__translate_item_parts(self,
                                        orig_start: Optional[str],
                                        orig_stop: Optional[str],
                                        orig_step: str,
                                        is_range: bool) -> Tuple[Optional[int], Optional[int], float]:
        """ Translate the specification item parts into numeric forms
        """

        # translate the start:
        start = Specifications.transform_empty_string(orig_start)
        start = self.transform_name(start)
        start = self.transform_negative_number(start, is_range)
        if start is not None and not comm.isnumeric(start):
            raise UnidentifiableNonNumericSpec(f'Do not know how to interpret: {start}')
        int_start = int(start) if start is not None else None
        #pp(f'{int_start=}')

        # translate the stop:
        stop = self.transform_empty_string(orig_stop)
        stop = self.transform_name(stop)
        stop = self.transform_negative_stop_number(stop, is_range)
        stop = self.validate_positive_number(stop, is_range)
        if stop is not None and not comm.isnumeric(stop):
            raise UnidentifiableNonNumericSpec(f'Do not know how to interpret: {stop}')
        int_stop = int(stop) if stop is not None else None

        # translate the step:
        step = self.transform_empty_string(orig_step)
        if step is not None and not comm.isnumeric(step):
            raise UnidentifiableNonNumericSpec(f'Do not know how to interpret: {step}')
        float_step = float(step) if step is not None else 1.0

        return int_start, int_stop, float_step


    def phase_three__resolve_dependencies(self,
                                          start: Optional[int],
                                          stop: Optional[int],
                                          step: float,
                                          is_range: bool):
        """Resolve any transformations that depend on multiple parts
        """
        int_start = self.transform_none_start(start, step)
        int_stop = self.transform_none_stop(int_start, stop, step, is_range)
        return int_start, int_stop, step


    @staticmethod
    def transform_empty_string(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        elif val.strip() == '':
            return None
        else:
            return val


    def transform_name(self,
                       val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        if comm.isnumeric(val):
            return val
        if self.header is None:
            raise UnidentifiableNonNumericSpec(f'Do not know how to interpret: {val}')
        try:
            position = str(self.header.get_field_position(val.strip()))
        except KeyError:
            comm.abort(f'Error: Invalid string in spec: {val}',
                        f'Not in header list: {self.header.field_names}')
        return position


    def transform_negative_number(self,
                                  val: Optional[str],
                                  is_range: bool) -> Optional[str]:

        if val is None or int(val) >= 0:
            return val

        int_val = int(val)

        if self.infile_item_count is None:
            raise NegativeOffsetWithoutItemCountError

        adjusted_val = self.infile_item_count + int_val + 1
        if adjusted_val < 0:
            if is_range:
                result = max(adjusted_val, 0)
            else:
                raise OutOfRangeError
        else:
            result = adjusted_val
        return str(result)


    def transform_negative_stop_number(self,
                                       val: Optional[str],
                                       is_range: bool) -> Optional[str]:

        if val is None or int(val) >= 0:
            return val

        int_val = int(val)

        if self.infile_item_count is None:
            raise NegativeOffsetWithoutItemCountError

        adjusted_val = self.infile_item_count + int_val + 1
        if adjusted_val < 0:
            if is_range:
                result = max(adjusted_val, -1)
            else:
                raise OutOfRangeError
        else:
            result = adjusted_val
        return str(result)




    def validate_positive_number(self,
                          val: Optional[str],
                          is_range: bool) -> Optional[str]:

        #pp('|------------------- validate_positive_number --------------------|')
        #pp(f'{val=}')
        if val is None:
            return val
        elif int(val) <= 0:
            return val
        elif self.infile_item_count is None:
            return val
        elif self.infile_item_count is None:
            return val

        if int(val)  > self.infile_item_count:
            if is_range:
                return val
            else:
                raise OutOfRangeError
        else:
            return val


    def transform_none_start(self,
                             start: Union[int, None],
                             step: float) -> int:
        """
        Example Sources:
            - -r 1
            - -r 3:
            - -r 3:4
            - -r :3
            - -r '::'
            - -r '::2'
        """
        assert start is None or comm.isnumeric(start)
        if comm.isnumeric(start):
            assert(isinstance(start, int))
            return start

        # Start=None - which is *always* a range (unlike stop)
        if step >= 0:
            int_start = 0
        else:
            if self.infile_item_count is None:
                raise NegativeStepWithoutItemCountError
            else:
                int_start = self.infile_item_count

        return int_start


    def transform_none_stop(self,
                            start: int,
                            stop: Optional[int],
                            step: float,
                            is_range: bool) -> int:

        assert stop is None or comm.isnumeric(stop)
        if comm.isnumeric(stop):
            assert(isinstance(stop, int))
            return stop

        if is_range:
            if step >= 0:
                if self.infile_item_count is None:
                    # fixme: determine impacts of this (extra big indexes?)
                    int_stop = 999
                    #int_stop = None # experiment!
                    #raise UnboundedStopWithoutItemCountError
                else:
                    int_stop = self.infile_item_count + 1
            else:
                int_stop = -1
        else:
            if step >= 0:
                int_stop = start + 1
            else:
                int_stop = start -1

        return int_stop



    def has_everything(self) -> bool:
        assert self.specs_strings != []
        return self.specs_strings == [':']


    def has_all_inclusions(self) -> bool:
        return self.spec_type in ('incl_col', 'incl_rec') and self.specs_strings in ([':'], ['::1'], ['::-1'])


    def has_exclusions(self) -> bool:
        return self.spec_type in ('excl_col', 'excl_rec') and self.specs_final != []




class Indexer:

   def __init__(self,
                specs,
                item_count: Optional[int]=None):

       assert item_count is None or item_count > -1

       self.specs = specs
       self.item_max = MAX_INDEX_REC_CNT
       self.item_count = item_count
       self.index = []
       self.valid = True

       assert self.item_max is not None and self.item_max > -1

       self.nop = False
       self.includes_reverse = False
       self.includes_repeats = False
       self.includes_out_of_order = False
       self.index_count = 0
       self.prior_max = -1



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
       specs = self.specs # lets make this a local ref for speed
       index = []

       for rec in specs:

           if rec.is_full_step():
               range_index = self._expand_one_fullstep_range(rec)
               index += range_index
           elif rec.is_random_step():
               range_index = self._expand_one_random_range(rec)
               index += range_index
           else:
                comm.abort('Error! Invalid specification step',
                           f'step: {step_part} is invalid')

       self.index = index
       if self.nop:
           self.valid = False
           self.index = []

       #pp(f'{self.includes_out_of_order=}')
       #pp(f'{self.includes_repeats=}')
       #pp(f'{self.includes_reverse=}')
       #pp(f'{self.valid=}')
       #pp(f'{self.index=}')
       #print('\n********************************************************')


   def _expand_one_fullstep_range(self,
                                  rec) -> List[int]:

        nop = self.nop
        reverse = self.includes_reverse
        repeats = self.includes_repeats
        out_of_order = self.includes_out_of_order
        item_max = self.item_max
        count = self.index_count
        prior_max = self.prior_max
        index = []

        if rec.step < 0:
            reverse = True
        if rec.is_sysmaxsize_stop():
            nop = True
        if nop and (out_of_order or repeats or reverse):
            pass
        else:
            for part in range(rec.start, rec.stop, int(rec.step)):
                assert part > -1

                if abs(part) < prior_max:
                    out_of_order = True
                elif abs(part) == prior_max:
                    repeats = True
                prior_max = abs(part)

                count += 1
                if count > item_max:      # limits index to max mem size
                    nop = True
                elif not nop:
                    index.append(part)

        self.nop = nop
        self.includes_reverse = reverse
        self.includes_repeats = repeats
        self.includes_out_of_order = out_of_order
        self.index_count = count
        self.prior_max = prior_max

        return index


   def _expand_one_random_range(self,
                                  rec) -> List[int]:

        nop = self.nop
        reverse = self.includes_reverse
        repeats = self.includes_repeats
        out_of_order = self.includes_out_of_order
        item_max = self.item_max
        count = self.index_count
        prior_max = self.prior_max
        index = []

        if rec.step < 0:
            reverse = True
        if rec.is_sysmaxsize_stop():
            nop = True
        if nop and (out_of_order or repeats or reverse):
            pass
        else:
            multiplier = 1 if rec.step > 0 else -1
            for part in range(rec.start, rec.stop, 1*multiplier):
                assert part > -1

                result = random.random()
                if abs(rec.step) > result:
                    if abs(part) < prior_max:
                        out_of_order = True
                    elif abs(part) == prior_max:
                        repeats = True
                    prior_max = abs(part)

                    count += 1
                    if count > item_max:
                        nop = True
                    elif not nop:
                        index.append(part)

        self.nop = nop
        self.includes_reverse = reverse
        self.includes_repeats = repeats
        self.includes_out_of_order = out_of_order
        self.index_count = count
        self.prior_max = prior_max

        return index






   def has_repeats(self) -> bool:
       # Lets assume that there may be repeats if the index build failed:
       if not self.valid:
           return False

       # Only works if specs_expanded has been populated!
       if len(set(self.index)) != len(self.index):
           return True

       return False



def includes_all_or_none(specs) -> bool:
    """
    """
    if len(specs) == 0:
        return True
    elif len(specs) == 1 and specs[0].strip() in ('', ':', '::-1', '::1'):
        return True
    return False



def is_index_out_of_order(index) -> bool:
    """
    Considers either mixed-order or reverse order True
    Note: if the index is empty - because its build failed (too big?) this will return True!
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



class ItemCountTooBigException(Exception):
    pass

class NegativeOffsetWithoutItemCountError(Exception):
    pass

class NegativeStepWithoutItemCountError(Exception):
    pass

class OutOfRangeError(Exception):
    pass

class UnidentifiableNonNumericSpec(Exception):
    pass

class UnboundedStopWithoutItemCountError(Exception):
    pass
