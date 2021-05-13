import operator
from pprint import pprint as pp
import sys
from typing import Any, Dict, List, Tuple

import datagristle.file_io as file_io


class ColSetFreaker(object):

    def __init__(self,
                 input_handler,
                 output_handler,
                 col_type: str,
                 number: int,
                 sampling_method: str,
                 sampling_rate: float,
                 sort_order: str,
                 sort_col: int,
                 max_key_len: int) -> None:

        self.input_handler = input_handler
        self.output_handler = output_handler
        self.col_type = col_type
        self.number = number
        self.sampling_method = sampling_method
        self.sampling_rate = sampling_rate
        self.sort_order = sort_order
        self.sort_col = sort_col
        self.max_key_len = max_key_len

        self.col_len_tracker: ColumnLengthTracker = None
        self.field_freq: Dict[Any, Any] = {}
        self.sorted_freq: List[Any] = None
        self.truncated: bool = None


    def create_freq_from_column_set(self, col_set: List[int]) -> None:

        #----- calculate field lengths -----
        self.build_freq(col_set)

        #----- sort the field_freq ------
        revorder = (True if self.sort_order == 'reverse' else False)
        self.sorted_freq = sorted(self.field_freq.items(),
                                key=operator.itemgetter(self.sort_col),
                                reverse=revorder)

        #----- calculate field lengths for output formmating -----
        self.col_len_tracker = ColumnLengthTracker()
        self.col_len_tracker.add_all_values(self.sorted_freq)
        self.col_len_tracker.trunc_all_col_lengths(self.max_key_len)


    def build_freq(self, columns: List[int]) -> None:
        """ Inputs:
                - columns    - list of columns to put into key
            Updates instance variables:
                - freq_dict  - freq distribution dict - can be empty if column
                               doesn't exist in file.  This happens when user
                               is doing a freq on "each" columns.
                - truncated  - True/False boolean that indicates if the dict was truncated
                Tested via test-harness
        """
        freq_cnt = 0
        self.field_freq = {}
        self.truncated = False

        def process_rec(record: List[str]) -> None:
            nonlocal freq_cnt
            if self.sampling_method == 'interval':
                if (self.input_handler.rec_cnt+1) % self.sampling_rate != 0:
                    return
            key = self._create_key(record, columns)
            if key:
                try:
                    self.field_freq[key] += 1
                except KeyError:
                    self.field_freq[key] = 1
                    freq_cnt += 1
                    if freq_cnt >= self.number:
                        self.truncated = True
                        print('WARNING: freq dict is too large - will truncate')
                        raise TooLargeError

        for rec in self.input_handler:
            try:
                process_rec(rec)
            except TooLargeError:
                break


    def _create_key(self,
                    fields: List[str],
                    required_field_indexes: List[int]) -> Tuple[str, ...]:
        """ input:
                - fields - a single record in the form of a list of fields
                - required_field_indexes - identifies which fields to put into output key
                output:
                - the required fields from fields in tuple format.
                Tested via test-harness.
        """
        if self.col_type == 'all':
            return tuple(fields)

        key = []
        for field_idx in required_field_indexes:
            try:
                key.append(fields[field_idx].strip())
            except IndexError:
                break # is probably freaking all cols with 'each' option.
        return tuple(key)



    def write_output(self,
                     output: file_io.OutputHandler,
                     write_limit: int,
                     col_set_num: List[int]):

        write_cnt = 0
        for key_tup in self.sorted_freq:
            write_cnt += 1
            if write_limit and write_cnt > write_limit:
                break
            row = self.format_output_row(key_tup, col_set_num)
            output.write_rec(row)   # type: ignore


    def format_output_row(self,
                          freq_tup: Tuple[Tuple[str, ...], int],
                          col_set_num: List[int]) -> str:
        """ input:
            - freq_tup - is a tuple consisting of two entries: key & count.
                Each key is also a tuple.  So it looks like this:
                    (('key1a', 'key1b', 'key1c'), 5   )
            output:
            - an entire row to be written as output
            tested via test-harness
        """
        if self.col_type == 'each':
            assert len(col_set_num) == 1
            key_label = 'col:%03d - ' % col_set_num[0]
        else:
            key_label = ''

        key_part = ''
        for colnum, key in enumerate(freq_tup[0]):
            key_string = ' %-*.*s  - ' % (self.col_len_tracker.max_dict[colnum],
                                          self.col_len_tracker.max_dict[colnum],
                                          key)
            key_part += key_string
        row = '%s%s %s\n' % (key_label, key_part, freq_tup[1])
        return row





class ColumnLengthTracker(object):
    """ Tracks the maximum key length for each column.
        This is useful later when printing columns - in order to keep them
        of consistent widths for each record.
        Tested via test harness.
    """
    def __init__(self):
        self.max_dict: Dict[int, int] = {}

    def add_val(self, col_num: int, value: str) -> None:
        """ Update tracked max length for a given column if the new value
            is greater than the old value.
            Inputs:
                 - col_num:  is the position of the column within the key
                 - value:    is the actual column value
            Outputs:
                 - none:     it updates the internal object length dictionary
        """
        try:
            if len(value) > self.max_dict[col_num]:
                self.max_dict[col_num] = len(value)
        except KeyError:
            self.max_dict[col_num] = len(value)

    def add_all_values(self, freq_list: List[Tuple[Tuple[str, ...], int]]) -> None:
        """ Step through a list of tuples which the key is a tuple of 1-many
            parts, and the value is the count.  For each part of the key call
            the add_val function to then store the max length.
        """
        for keyval_tup in freq_list:
            keys = keyval_tup[0]
            for index, key in enumerate(keys):
                self.add_val(index, key)

    def trunc_all_col_lengths(self, maxkeylen: int) -> None:
        """ Gradually reduces the length of columns, reducing the longest one
            before the shorter ones.
        """
        while (self._get_tot_col_len() - maxkeylen) > 0:
            max_key = max(self.max_dict, key=self.max_dict.get)
            self.max_dict[max_key] -= 1

    def _get_tot_col_len(self) -> int:
        """ Returns the total column length by adding together to the longest
            column value of each column.
        """
        return sum(list(self.max_dict.values()))


class TooLargeError(Exception):
    pass
