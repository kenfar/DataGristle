#!/usr/bin/env python
import csv
import functools
import os
from pprint import pprint as pp
import tempfile
import time
from typing import List, Tuple, Dict, Any, Optional, IO, Hashable

import datagristle.common as comm
import datagristle.configulator as conf
from datagristle import file_io
import datagristle.slice_specs as slicer


MAX_MEM_INDEX_CNT = 20_000_000



class SliceRunner:

    def __init__(self,
                 config_manager,
                 nconfig) -> None:

        self.config_manager = config_manager
        self.nconfig = nconfig

        self.input_handler: file_io.InputHandler
        self.output_handler: file_io.OutputHandler
        self.temp_fn = None

        self.rec_cnt = None
        self.col_cnt = None

        self.rec_specs: slicer.Specifications
        self.exrec_specs: slicer.Specifications
        self.col_specs: slicer.Specifications
        self.excol_specs: slicer.Specifications

        self.incl_rec_slicer: slicer.SpecProcessor
        self.excl_rec_slicer: slicer.SpecProcessor
        self.incl_col_slicer: slicer.SpecProcessor
        self.excl_col_slicer: slicer.SpecProcessor
        self.valid_rec_spec = None
        self.valid_col_spec = None

        self.rec_index = None
        self.col_index = None

        self.mem_limiter = comm.MemoryLimiter(max_mem_gbytes=nconfig.max_mem_gbytes)


    def setup_stage1(self) -> None:
        self._setup_files()


    def setup_stage2(self) -> None:
        try:
            self._setup_specs()
        except (slicer.NegativeOffsetWithoutItemCountError,
                slicer.NegativeStepWithoutItemCountError,
                slicer.UnboundedStopWithoutItemCountError) as err:
            if self.are_infiles_from_stdin():
                self._write_stdin_to_file()
                self.nconfig, _ = self.config_manager.get_config(self.temp_fn)
            self._setup_counts()
            try:
                self._setup_specs()
            except (slicer.NegativeOffsetWithoutItemCountError,
                    slicer.NegativeStepWithoutItemCountError,
                    slicer.UnboundedStopWithoutItemCountError):
                comm.abort('Error: unable to count rows in file to resolve config references!',
                        f'Record count: {self.rec_cnt}, Column count: {self.col_cnt}',
                        verbosity='debug')

        self._setup_slicers()
        self.rec_index = RecIndexOptimization(self.incl_rec_slicer,
                                              self.excl_rec_slicer,
                                              self.nconfig.verbosity)
        self.col_index = ColIndexOptimization(self.incl_col_slicer,
                                              self.excl_col_slicer,
                                              self.is_optimized_for_all_cols(),
                                              self.nconfig.verbosity)

        self._pp(' ')
        self._pp('Stage2 Optimizations: ')
        self._pp(f'    is_optimized_for_all_recs: {self.is_optimized_for_all_recs()}')
        self._pp(f'    is_optimized_with_rec_index: {self.rec_index.is_valid}')
        self._pp(f'    rec_index_optimization_stop_rec: {self.rec_index.stop_rec}')

        self._pp(f'    is_optimized_for_all_cols: {self.is_optimized_for_all_cols()}')
        self._pp(f'    is_optimized_with_col_index: {self.col_index.is_valid}')


    def _write_stdin_to_file(self):
        start_time = time.time()

        assert self.nconfig.infiles[0] == '-'
        _, self.temp_fn = tempfile.mkstemp(prefix='gristle_slicer_stdin_temp_')
        with open(self.temp_fn, 'w', newline='', encoding='utf-8') as outbuf:
            writer = csv.writer(outbuf)
            writer.writerows(self.input_handler)
        self.input_handler = file_io.InputHandler([self.temp_fn],
                                                  self.nconfig.dialect,
                                                  return_header=True)

        self._pp(f'--------> write_stdin_to_file duration: {time.time() - start_time:.2f}')


    def _pp(self,
            val: Any) -> None:
        if self.nconfig.verbosity == 'debug':
            print(val)


    def shutdown(self) -> None:
        self.input_handler.close()
        self.output_handler.close()

        if self.temp_fn:
            os.remove(self.temp_fn)

        file_io.remove_all_temp_files(prefix='gristle_slicer_stdin_temp', min_age_hours=1)


    def _setup_files(self) -> None:
        self.input_handler = file_io.InputHandler(self.nconfig.infiles,
                                                  self.nconfig.dialect,
                                                  return_header=True)
        self.output_handler = file_io.OutputHandler(self.nconfig.outfile,
                                                    self.input_handler.dialect)


    def _setup_counts(self) -> None:
        start_time = time.time()
        if self.temp_fn:
            self.rec_cnt = file_io.get_rec_count([self.temp_fn], self.input_handler.dialect)
        else:
            self.rec_cnt = file_io.get_rec_count(self.nconfig.infiles, self.input_handler.dialect)

        self.col_cnt = len(self.nconfig.header.field_names)
        if self.col_cnt < 0:
            self.col_cnt = None
        if self.nconfig.verbosity == 'debug':
            print(f'--------> setup_counts  duration: {time.time() - start_time:.2f}')



    def _setup_specs(self) -> None:
        """ Will get run multiple times - as more info trickles in!
        """

        # record specs:
        records = self.nconfig.records.split(',')
        exrecords = self.nconfig.exrecords.split(',') if self.nconfig.exrecords else []
        self.rec_specs = slicer.Specifications('incl_rec',
                                                records,
                                                infile_item_count=self.rec_cnt)
        self.exrec_specs = slicer.Specifications('excl_rec',
                                                 exrecords,
                                                 infile_item_count=self.rec_cnt)

        # col specs:
        records = self.nconfig.columns.split(',')
        exrecords = self.nconfig.excolumns.split(',') if self.nconfig.excolumns else []
        self.col_specs = slicer.Specifications('incl_col',
                                                records,
                                                infile_item_count=self.col_cnt,
                                                header=self.nconfig.header)
        self.excol_specs = slicer.Specifications('excl_col',
                                                 exrecords,
                                                 infile_item_count=self.col_cnt,
                                                 header=self.nconfig.header)


    def _setup_slicers(self) -> None:
        self.incl_rec_slicer = slicer.SpecProcessor(self.rec_specs)
        self.excl_rec_slicer = slicer.SpecProcessor(self.exrec_specs)
        self.incl_col_slicer = slicer.SpecProcessor(self.col_specs)
        self.excl_col_slicer = slicer.SpecProcessor(self.excol_specs)


    def is_optimized_for_all_recs(self) -> bool:
        return bool(self.incl_rec_slicer.has_all_inclusions is True
                    and self.excl_rec_slicer.has_exclusions is False)

    def is_optimized_for_all_cols(self) -> bool:
        return bool(self.incl_col_slicer.has_all_inclusions is True
                    and self.excl_col_slicer.has_exclusions is False)


    def process_data(self) -> None:
        start_time = time.time()
        if self.must_process_in_memory():
            self.process_recs_in_memory()
        else:
            self.process_recs_from_file()
        self._pp(f'--------> process_data duration: {time.time() - start_time:.2f}')


    def must_process_in_memory(self) -> bool:

        if (self.incl_rec_slicer.includes_out_of_order
                or self.incl_rec_slicer.includes_repeats
                or self.incl_rec_slicer.includes_reverse):

            if self.rec_index.is_valid:
                return True
            elif self.is_optimized_for_all_recs():
                return True
            else:
                comm.abort('Error: There are out of order, reverse, or repeating rec specs but cannot fit into memory!',
                verbosity='debug')

        return False



    def process_recs_from_file(self) -> None:
        """ Reads the file one record at a time, compares against the
            specification, and then writes out qualifying records and
            columns.
            Args:
                - input_handler
                - output_handler
                - incl_rec_spec
                - excl_rec_spec
                - merged_rec_spec: simple list of which recs to slice
                - merged_col_spec: simple list of which columns to slice
        """
        self._pp(f'process: process_recs_from_file')
        next_index_sub = 0

        for rec_number, rec in enumerate(self.input_handler):

            if self.is_optimized_for_all_recs():
                pass
            elif self.rec_index.is_valid:
                if rec_number > self.rec_index.stop_rec:
                    if self.are_infiles_from_stdin():
                        # Need to finish reading from file rather than break so that we don't
                        # break pipe for pgm piping data to us.  We'll spin thru the rest of 
                        # the recs as quickly as possible, doing it all right here is about 20%
                        # faster than going thru the main loop:
                        break
                        for _ in self.input_handler:
                            pass
                        break
                    else:
                        break

                try:
                    if rec_number == self.rec_index.index[next_index_sub]:
                        next_index_sub += 1
                    else:
                        continue
                except IndexError:
                    continue

            else:
                if not self.incl_rec_slicer.specs_evaluator(rec_number):
                    continue
                elif self.excl_rec_slicer.specs_evaluator(rec_number):
                    continue

            output_rec = []

            if self.is_optimized_for_all_cols():
                output_rec = rec
            elif self.col_index.is_valid:
                output_rec = self.get_cols_from_index(rec,
                                                      self.col_index.index)
                if self.col_index.col_default_range:
                    self.col_index.prune_index(actual_col_cnt=len(rec))
            else:
                output_rec = self.get_cols_from_eval(rec,
                                                     len(rec),
                                                     self.incl_col_slicer,
                                                     self.excl_col_slicer)

            if output_rec:
                self.output_handler.write_rec(record=output_rec)



    def process_recs_in_memory(self) -> None:
        """ Reads the entire file into memory, then processes one record
            at a time, compares against the specification, and then writes
            out qualifying records and columns.
        """
        self._pp(f'process: process_recs_in_memory')

        if self.incl_rec_slicer.indexer.valid is False:
            comm.abort('Unable to process in memory', 'incl_rec.indexer.invalid')
        if self.excl_rec_slicer.indexer.valid is False:
            comm.abort('Unable to process in memory', 'excl_rec.indexer.invalid')

        all_rows = []

        rec: List[str] = []
        for rec_number, rec in enumerate(self.input_handler):
            if rec_number > self.rec_index.stop_rec:
                if self.are_infiles_from_stdin():
                    for _ in self.input_handler:
                        pass
                    break
                else:
                    break
            all_rows.append(rec)
            try:
                self.mem_limiter.check_record(rec, rec_number)
            except MemoryError:
                comm.abort('ERROR: too many rows to fit into memory',
                            'Change options to either process_by_file or break the process into multiple steps')

        # if we originally couldn't get col counts because of stdin,
        # update now that we have it all loaded into a list:
        if self.col_cnt in (None, -1):
            self.col_cnt = len(all_rows[0]) - 1
        assert self.col_cnt > -1

        for rec_num in self.rec_index.index:
            output_rec = []
            try:
                if self.is_optimized_for_all_cols():
                    output_rec = all_rows[rec_num]
                elif self.col_index.is_valid:
                    output_rec = self.get_cols_from_index(all_rows[rec_num],
                                                          self.col_index.index)
                else:
                    # The slower fallback eval solution:
                    output_rec = self.get_cols_from_eval(all_rows[rec_num],
                                                         self.col_cnt,
                                                         self.incl_col_slicer,
                                                         self.excl_col_slicer)
            except IndexError:
                pass
            if output_rec:
                self.output_handler.write_rec(record=output_rec)



    def get_cols_from_index(self,
                            input_rec: List[str],
                            col_index: List[int]) -> List[str]:
        """ Slightly faster solution (about 20% faster) than evals, but requires
            more memory.
        """
        output_rec = []
        for col_number in col_index:
            try:
                output_rec.append(input_rec[col_number])
            except IndexError:
                pass # maybe a short record, or user provided a spec that exceeded cols
        return output_rec


    def get_cols_from_eval(self,
                           input_rec: List[str],
                           col_count: int,
                           incl_col_slicer: slicer.SpecProcessor,
                           excl_col_slicer: slicer.SpecProcessor) -> List[str]:
        """ Primarily used for unbounded col ranges with stdin
            About 20% slower than get_cols_from_index()
            WARNING: is this actually safe?  does it process in the right order?
        """
        #fixme: do we need to ensure that this is only used with cols in order?!?!?!?!
        output_rec = []
        for col_number in range(0, col_count):
            if self.cached_col_eval(col_number, incl_col_slicer, excl_col_slicer):
                output_rec.append(input_rec[col_number])
        return output_rec


    @functools.lru_cache
    def cached_col_eval(self,
                        col_number: int,
                        incl_col_slicer,
                        excl_col_slicer) -> bool:
        """ The caching on this eval speeds it up 50-75% on large files
            with many columns
        """
        if incl_col_slicer.specs_evaluator(location=col_number):
            if not excl_col_slicer.specs_evaluator(location=col_number):
                return True
        return False


    def are_infiles_from_stdin(self) -> bool:
        return bool(self.nconfig.infiles == ['-'])



class RecIndexOptimization:

    def __init__(self,
                 incl_rec_slicer,
                 excl_rec_slicer,
                 verbosity):

        self.incl_rec_slicer = incl_rec_slicer
        self.excl_rec_slicer = excl_rec_slicer
        self.verbosity = verbosity

        self.index: List[int] = []
        self.stop_rec: int = 0
        self.is_valid = False

        start_time = time.time()
        self.build_index()
        self.duration = time.time() - start_time

        if verbosity == 'debug':
            self.print_stats()


    def build_index(self):

        if (self.incl_rec_slicer.indexer.valid
        and self.excl_rec_slicer.indexer.valid
        and len(self.excl_rec_slicer.index) <= 10_000):
        # Pulling this out until we can figure out how to process in mem in reverse order without index
        #and self.is_optimized_for_all_recs() is False
            for spec_item in self.incl_rec_slicer.index:
                if spec_item in self.excl_rec_slicer.index:
                    continue
                else:
                    if len(self.index) > MAX_MEM_INDEX_CNT:
                        self.index = []
                        break
                    self.index.append(spec_item)
            else:
                self.stop_rec = max(self.index, default=0)
                self.is_valid = True


    def print_stats(self):

        print(' ')
        print('Column-Index Optimizations: ')
        print(f'    {self.incl_rec_slicer.has_all_inclusions=}')
        print(f'    {self.incl_rec_slicer.indexer.valid=}')
        print(f'    {len(self.incl_rec_slicer.index)=}')
        print(f'    {self.incl_rec_slicer.includes_out_of_order=}')
        print(f'    {self.incl_rec_slicer.includes_repeats=}')
        print(f'    {self.incl_rec_slicer.includes_reverse=}')
        print(' ')
        print(f'    {self.excl_rec_slicer.has_all_inclusions=}')
        print(f'    {self.excl_rec_slicer.indexer.valid=}')
        print(f'    {len(self.excl_rec_slicer.index)=}')
        print(' ')
        print(f'--------> setup_index_optimization  duration: {self.duration:.2f}')



class ColIndexOptimization:

    def __init__(self,
                 incl_col_slicer,
                 excl_col_slicer,
                 is_optimized_for_all_cols,
                 verbosity):

        self.incl_col_slicer = incl_col_slicer
        self.excl_col_slicer = excl_col_slicer
        self.verbosity = verbosity

        self.index: List[int] = []
        self.is_valid = False
        self.col_default_range: bool

        start_time = time.time()
        self.build_index(is_optimized_for_all_cols)
        self.duration = time.time() - start_time

        if verbosity == 'debug':
            self.print_stats()


    def build_index(self,
                    is_optimized_for_all_cols):

        if (self.incl_col_slicer.indexer.valid
        and self.excl_col_slicer.indexer.valid
        and is_optimized_for_all_cols is False):
            for spec_item in self.incl_col_slicer.index:
                if spec_item in self.excl_col_slicer.index:
                    continue
                else:
                    if len(self.index) > MAX_MEM_INDEX_CNT:
                        self.index = []
                        break
                    self.index.append(spec_item)
            else:
                self.is_valid = True
        self.col_default_range = self.incl_col_slicer.indexer.col_default_range


    def print_stats(self):

        print(' ')
        print('Column-Index Optimizations: ')
        print(f'    {self.incl_col_slicer.indexer.valid=}')
        print(f'    {self.excl_col_slicer.indexer.valid=}')
        print(f'--------> setup_index_optimization  duration: {self.duration:.2f}')

    def prune_index(self,
                    actual_col_cnt: int):
        new_index = []
        new_index = [x for x in self.index if x <= actual_col_cnt]
        self.index = new_index
        self.col_default_range = False





class TooMuchDataError(Exception):
    pass
