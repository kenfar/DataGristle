#!/usr/bin/env python
""" Applies a list of python slicing specifications to a number to determine if
    that number meets the specifications or not.

    Typical Usage:
        >>> sp = location_slicer.SpecProcessor(specs=['1','5','10:20','70:-1'])
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

    Contents:
        - SpecRecord
            - desc: a pydantic data class that defines a single spec record
        - Specifications
            - creates a list of SpecRecords
        - SpecProcessor
            - runs the Indexer
        - Indexer
            - reads a list of SpecRecords

    This source code is protected by the BSD license.  See the file "LICENSE"
    in the source code root directory for the full language or refer to it here:
       http://opensource.org/licenses/BSD-3-Clause
    Copyright 2011-2022 Ken Farmer
"""

import copy
import functools
import more_itertools
from pprint import pprint as pp
import re
import random
import sys
from typing import List, Dict, Tuple, Union, Any, Optional, Type

from pydantic.dataclasses import dataclass
from pydantic import BaseModel, ValidationError, model_validator, field_validator

import datagristle.common as comm
import datagristle.csvhelper as csvhelper

MAX_INDEX_REC_CNT = 20_000_000
DEFAULT_COL_RANGE_STOP = 5_000
DEFAULT_REC_RANGE_STOP = sys.maxsize




class SpecRecord(BaseModel):
    """ Defines a single specification record.

    A run of the program may have multiple spec records in a list.

    Args:
        start: an integer from 0-n
        stop:  an integer from 0-n, normally > than start, but must be < start if the step is < 0$a
        step:  a float: can be positive, negative, or a decimal.  Cannot be 0.
        spec_type: one of ('incl_rec', 'excl_rec', 'incl_col', 'excl_col')
        col_default_range: True or False
    """


    start:      int
    stop:       int
    step:       float
    spec_type:  str
    col_default_range: bool
    rec_default_range: bool

    @field_validator('start')
    def start_must_be_positive(cls, val) -> int:
        if val < 0:
            comm.abort('start must be >= 0')
        return val

    @field_validator('stop')
    def stop_must_be_positive(cls, val) -> int:
        if val < -1:
            comm.abort(f'stop must be >= 0, is {val}')
        return val

    @field_validator('step')
    def step_must_be_nonzero(cls, val) -> float:
        if val == 0:
            comm.abort('step must be non-zero')
        return val

    @model_validator(mode='before')
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

    @model_validator(mode='before')
    def limit_steps_to_inclusions(cls, values: Dict) -> Dict:
        spec_type = values.get('spec_type')
        step = values.get('step')
        if spec_type not in ('incl_rec', 'incl_col'):
            if step != 1.0:
                comm.abort(f'Error: exclusion spec is not allowed to have steps: {step}')
        return values

    @model_validator(mode='before')
    def limit_col_default_range_to_cols(cls, values: Dict) -> Dict:
        spec_type = values.get('spec_type')
        col_default_range = values.get('col_default_range')

        if col_default_range and spec_type not in ('incl_col', 'excl_col'):
             comm.abort(f'Error: col_default_range set for a record spec')
        return values

    @model_validator(mode='before')
    def limit_rec_default_range_to_recs(cls, values: Dict) -> Dict:
        spec_type = values.get('spec_type')
        rec_default_range = values.get('rec_default_range')

        if rec_default_range and spec_type not in ('incl_rec', 'excl_rec'):
             comm.abort(f'Error: rec_default_range set for a column spec')
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
    """ Manages the evaluation of record numbers against spec for a single spec_type

    It uses the Specification List[SpecRecord] structure as input and supports the
    evaluation of col or row numbers aginst these specs.
    """

    def __init__(self,
                 specs) -> None:
        """
        Args:
            specs: a List of SpecRecords

        Public Methods:
            specs_evaluator: evaluates an offset against the list of specs

        Notes:
            Automatically generates self.index - which is a list of offsets. This
            supports a fast alternative method of evaluating cols & recs.
        """
        self.specs = specs

        self.has_exclusions = specs.has_exclusions()
        self.has_all_inclusions = specs.has_all_inclusions()

        self.indexer = Indexer(self.specs.specs_final)
        self.indexer.builder()
        self.index = self.indexer.index
        self.includes_out_of_order = self.indexer.includes_out_of_order
        self.includes_repeats = self.indexer.includes_repeats
        self.includes_reverse = self.indexer.includes_reverse



    def specs_evaluator(self,
                        location: int) -> bool:
        """ Evaluates a location offset against a spec list.

        Uses the python string slicing formats to specify valid ranges
            (all offset from 0):
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
                         spec: Type[SpecRecord],
                         location: int) -> bool:
        """ evaluates a single item against a location
        Args:
            - spec: a single SpecRecord
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
    """ Translates user spec strings into a List of SpecRecords

    For a single spec_type (ex: incl_rec), it will parse a string of specs
    into a list, translate this and store it as a List of SpecRecords in
    self.specs_final.

    Args:
        spec_type - one of ('incl_rec', 'excl_rec', 'incl_col', 'excl_col')
        specs_strings - big ex '3,6,15,22:28,30:35:2,40:50:-1'
        header - header object
        infile_item_count - count of cols or recs, needed for unbound ranges,
            etc

    Public attributes
        self.specs_final - List[SpecRecord] automatically generated by init
    """

    def __init__(self,
                 spec_type: str,
                 specs_strings: List[str],
                 header: Optional[csvhelper.Header] = None,
                 infile_item_count: int = None):

        self.spec_type = spec_type
        self.specs_strings = specs_strings
        self.header = header
        self.infile_item_count = infile_item_count

        assert spec_type in ['incl_rec', 'excl_rec', 'incl_col', 'excl_col']

        self.specs_final: List[SpecRecord] = self.specs_cleaner()


    def specs_cleaner(self) -> List[SpecRecord]:
        """ Returns a transformed version of the specs

        Returns:
            final_specs: List[SpecRecord]
            for specs that are empty   (ex: '') returns: []
            for specs that are default (ex: ':') returns: [SpecRecord]
        """

        if len(self.specs_strings) == 1:
            if self.specs_strings[0].strip() == '':
                self.specs_strings[0] = ':'

        final_specs = []
        for item in self.specs_strings:

            try:
                start, stop, step, is_range = self.phase1__item_parsing(item)

                int_start, int_stop, float_step = self.phase2__translate_item_parts(start, stop, step, is_range)

                (int_start, int_stop, float_step, col_default_range, rec_default_range) = self.phase3__resolve_deps(int_start,
                                                                                                                    int_stop,
                                                                                                                    float_step,
                                                                                                                    is_range)
                try:
                    final_rec = SpecRecord(start=int_start,
                                           stop=int_stop,
                                           step=float_step,
                                           spec_type=self.spec_type,
                                           col_default_range=col_default_range,
                                           rec_default_range=rec_default_range)
                except ValidationError as err:
                    comm.abort('Error: invalid specification',  f'{self.spec_type}: {start}:{stop}:{step}')
                final_specs.append(final_rec)
            except OutOfRangeError:
                continue
        return final_specs


    def phase1__item_parsing(self, item: str) -> Tuple[Optional[str], Optional[str], str, bool]:
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


    def phase2__translate_item_parts(self,
                                     orig_start: Optional[str],
                                     orig_stop: Optional[str],
                                     orig_step: str,
                                     is_range: bool) -> Tuple[Optional[int], Optional[int], float]:
        """ Translate the specification item parts into numeric forms
        """

        # translate the start:
        start = Specifications.transform_empty_string(orig_start)
        start = self.transform_name(start)
        start = self.transform_negative_start_number(start, is_range)
        if start is not None and not comm.isnumeric(start):
            raise UnidentifiableNonNumericSpec(f'Do not know how to interpret: {start}')
        int_start = int(start) if start is not None else None

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


    def phase3__resolve_deps(self,
                             start: Optional[int],
                             stop: Optional[int],
                             step: float,
                             is_range: bool):
        """Resolve any transformations that depend on multiple parts
        """
        int_start = self.transform_none_start(start, step)
        int_stop, col_default_range, rec_default_range = self.transform_none_stop(int_start, stop, step, is_range)
        return int_start, int_stop, step, col_default_range, rec_default_range


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


    def transform_negative_start_number(self,
                                        val: Optional[str],
                                        is_range: bool) -> Optional[str]:

        if val is None or int(val) >= 0:
            return val

        int_val = int(val)

        if self.infile_item_count is None:
            raise NegativeOffsetWithoutItemCountError

        adjusted_val = self.infile_item_count + int_val
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

        adjusted_val = self.infile_item_count + int_val
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

        if val is None:
            return val
        elif int(val) <= 0:
            return val
        elif self.infile_item_count is None:
            return val
        elif self.infile_item_count is None:
            return val

        if int(val)  >= self.infile_item_count:
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
                            is_range: bool) -> Tuple[int, bool, bool]:

        assert stop is None or comm.isnumeric(stop)
        col_default_range = False
        rec_default_range = False

        if comm.isnumeric(stop):
            assert(isinstance(stop, int))
            return stop, col_default_range, rec_default_range

        if is_range:
            if step >= 0:
                if self.infile_item_count is None:
                    if self.spec_type in ('incl_rec', 'excl_rec'):
                        int_stop = DEFAULT_REC_RANGE_STOP
                        rec_default_range = True
                    else:
                        int_stop = DEFAULT_COL_RANGE_STOP
                        col_default_range = True
                else:
                    int_stop = self.infile_item_count
            else:
                int_stop = -1
        else:
            if step >= 0:
                int_stop = start + 1
            else:
                int_stop = start -1

        return int_stop, col_default_range, rec_default_range


    def has_all_inclusions(self) -> bool:
        return bool(self.spec_type in ('incl_col', 'incl_rec') and self.specs_strings in ([':'], ['::1'], ['::-1']))


    def has_exclusions(self) -> bool:
        return bool(self.spec_type in ('excl_col', 'excl_rec') and self.specs_final)




class Indexer:
    """ Explodes the specification ranges into individual offsets.

    This function returns a list of all positions that are included within a
    specification - whether they're directly references, or they fall within
    a range.

    Args:
        item_count: the number of rows in the file or cols in the row.
            This value may be None if the calling pgm doesn't think we need to
            know what the last record is.

    Public Attributes:
        - self.index - List[int] - has the expanded specs, is empty if too large
        - self.valid - bool - is False if index is too large for mem
        - self.includes_reverse - bool
        - self.includes_repeats - bool
        - self.includes_out_of_order - bool
        - self.col_default_range - bool

    Notes:
        - If the index is too large for memory it will set self.index to [] and self.valid to False
    Raises:
        AssertionError - item-count is negative
    """

    def __init__(self,
                 specs):

        self._specs = specs
        self._item_max = MAX_INDEX_REC_CNT
        self._prior_max = -1
        self._nop = False
        self._index_count = 0

        self.index: List[int] = []
        self.valid = True
        self.includes_reverse = False
        self.includes_repeats = False
        self.includes_out_of_order = False
        self.col_default_range = False
        self.rec_default_range = False


    def builder(self):
        specs = self._specs # lets make this a local ref for speed
        index = []

        for rec in specs:

            if rec.rec_default_range:
                self.rec_default_range = True
                self.valid = False
                self.index = []
                return
            if rec.col_default_range:
                self.col_default_range = True
            index += self._expand_one_range(rec)

        self.index = index
        if self._nop:
            self.valid = False
            self.index = []


    def _expand_one_range(self,
                          rec) -> List[int]:
        """
        Note:
        - If too many rows are encountered it will enter a NOP mode, in which
          it keeps checking for data characteristics like repeating & out of order,
          but stops appending.  It does this because the index is unusable, which
          doesn't prevent processing - as long as there are no repeats, reverse, or
          out of order conditions.
        - We're copying some object variables into the function & then back again
          because it saves a ton of time on very large indexes.  A 10m row range takes
          9.5 seconds on my laptop this way vs 12.5 if we accessed them directly thru
          self.
        """

        nop = self._nop
        reverse = self.includes_reverse
        repeats = self.includes_repeats
        out_of_order = self.includes_out_of_order
        item_max = self._item_max
        count = self._index_count
        prior_max = self._prior_max
        index = []

        if rec.step < 0:
            reverse = True
        if rec.is_sysmaxsize_stop():
            nop = True
        if nop and (out_of_order or repeats or reverse):
            # no need to go further at this point - since we determined that we
            # can't complete the index and we also require one.
            pass
        else:
            if rec.is_full_step():
                range_step = int(rec.step)
            else:
                range_step = 1 if rec.step > 0 else -1

            for part in range(rec.start, rec.stop, range_step):
                assert part > -1

                if rec.is_random_step():
                    result = random.random()
                    if abs(rec.step) < result:
                        continue

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

        self._nop = nop
        self._index_count = count
        self._prior_max = prior_max
        self.includes_reverse = reverse
        self.includes_repeats = repeats
        self.includes_out_of_order = out_of_order

        return index




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

