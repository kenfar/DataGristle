#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""
from pprint import pprint as pp
from typing import List
import sys

import pytest

import datagristle.slice_specs as mod
import datagristle.csvhelper as csvhelper




class TestSpecRecord:

    def test_normal_happypath(self):
        spec_record = mod.SpecRecord(start=0, stop=3, step=1, spec_type='incl_rec',
                                     col_default_range=False, rec_default_range=False)
        spec_record = mod.SpecRecord(start=10, stop=20, step=2, spec_type='incl_col',
                                     col_default_range=True, rec_default_range=False)

    def test_invalid_spec_type(self):
        with pytest.raises(SystemExit):
            spec_record = mod.SpecRecord(start=10, stop=20, step=2, spec_type='blahblahblah',
                                        col_default_range=True, rec_default_range=False)

    def test_invalid_start_stop(self):
        with pytest.raises(SystemExit):
            spec_record = mod.SpecRecord(start=8, stop=1, step=1, spec_type='incl_rec',
                                         col_default_range=True, rec_default_range=False)

        with pytest.raises(SystemExit):
            spec_record = mod.SpecRecord(start=1, stop=8, step=-1, spec_type='incl_rec',
                                         col_default_range=True, rec_default_range=False)

    def test_zero_step(self):
        with pytest.raises(SystemExit):
            spec_record = mod.SpecRecord(start=1, stop=3, step=0, spec_type='incl_rec',
                                         col_default_range=True, rec_default_range=False)

    def test_steps_on_exclusions(self):
        with pytest.raises(SystemExit):
            spec_record = mod.SpecRecord(start=1, stop=3, step=2, spec_type='excl_rec',
                                         col_default_range=True, rec_default_range=False)

    def test_is_full_step(self):
        spec_record = mod.SpecRecord(start=1, stop=3, step=2, spec_type='incl_rec',
                                     col_default_range=False, rec_default_range=False)
        assert spec_record.is_full_step()

        spec_record = mod.SpecRecord(start=3, stop=1, step=-1, spec_type='incl_rec',
                                     col_default_range=False, rec_default_range=False)
        assert spec_record.is_full_step()

        spec_record = mod.SpecRecord(start=1, stop=3, step=0.25, spec_type='incl_rec',
                                     col_default_range=False, rec_default_range=False)
        assert spec_record.is_full_step() is False



class TestSpecificationsHelpers(object):

    def setup_spec(self,
                   specs_strings,
                   spec_type='incl_rec'):

        self.spec = mod.Specifications(spec_type=spec_type,
                                       specs_strings=specs_strings,
                                       header=None,
                                       infile_item_count=100)

    @pytest.mark.parametrize("spec_type", [("incl_rec"),  ("incl_col")])
    def test_has_all_inclusions_with_inclusions(self, spec_type):

        self.setup_spec(specs_strings=[':'], spec_type=spec_type)
        assert self.spec.has_all_inclusions() is True

        self.setup_spec(specs_strings=['1'], spec_type=spec_type)
        assert self.spec.has_all_inclusions() is False


    @pytest.mark.parametrize("spec_type", [("excl_rec"), ("excl_col")])
    def test_has_all_inclusions_with_exclusions(self, spec_type):

        self.setup_spec(specs_strings=[':'], spec_type=spec_type)
        assert self.spec.has_all_inclusions() is False

        self.setup_spec(specs_strings=['1'], spec_type=spec_type)
        assert self.spec.has_all_inclusions() is False


    @pytest.mark.parametrize("spec_type", [("incl_rec"),  ("incl_col")])
    def test_has_exclusions_on_inclusions(self, spec_type):

        self.setup_spec(specs_strings=[':'], spec_type=spec_type)
        assert self.spec.has_exclusions() is False

        self.setup_spec(specs_strings=[], spec_type=spec_type)
        assert self.spec.has_exclusions() is False


    @pytest.mark.parametrize("spec_type", [("excl_rec"), ("excl_col")])
    def test_has_exclusions_on_exclusions(self, spec_type):

        self.setup_spec(specs_strings=['1'], spec_type=spec_type)
        assert self.spec.has_exclusions() is True

        self.setup_spec(specs_strings=[], spec_type=spec_type)
        assert self.spec.has_exclusions() is False



class TestSpecificationsCleaner(object):

    def setup_spec(self,
                   specs_strings,
                   spec_type='incl_rec',
                   header: List[str] = None,
                   item_count=100):


        if header:
            header_obj = csvhelper.Header()
            header_obj.load_from_list(field_names=header)
        else:
            header_obj = None

        self.spec = mod.Specifications(spec_type=spec_type,
                                       specs_strings=specs_strings,
                                       header=header_obj,
                                       infile_item_count=item_count)

    def flatten_spec(self, element):
        start = self.spec.specs_final[element].start
        stop = self.spec.specs_final[element].stop
        step = self.spec.specs_final[element].step
        return (start, stop, step)


    def test_unbounded_start_and_stop(self):
        self.setup_spec(specs_strings=[':'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, 100, 1)

        self.setup_spec(specs_strings=['::'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, 100, 1)


    def test_unbounded_start(self):
        self.setup_spec(specs_strings=[':5'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, 5, 1)

        self.setup_spec(specs_strings=[':5:'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, 5, 1)


    def test_unbounded_stop(self):
        self.setup_spec(specs_strings=['5:'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (5, 100, 1)

        self.setup_spec(specs_strings=['5::'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (5, 100, 1)


    def test_too_many_colons(self):
        with pytest.raises(SystemExit) as excinfo:
            self.setup_spec(specs_strings=[':::'], spec_type='incl_rec')


    def test_multiple_single_cols(self):
        self.setup_spec(specs_strings=['3', '5', '7'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 3
        assert self.flatten_spec(0) == (3, 4, 1)
        assert self.flatten_spec(1) == (5, 6, 1)
        assert self.flatten_spec(2) == (7, 8, 1)


    def test_name_translation(self):
        self.setup_spec(specs_strings=['account_id'],
                        spec_type='incl_rec',
                        header=['account_id', 'customer_id'])
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, 1, 1)


    def test_invalid_name_translation(self):
        with pytest.raises(SystemExit) as excinfo:
            self.setup_spec(specs_strings=['account'],
                            spec_type='incl_rec',
                            header=['account_id', 'customer_id'])


    def test_negative_translation(self):
        self.setup_spec(specs_strings=['-1'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (99, 100, 1)


    def test_range(self):
        self.setup_spec(specs_strings=['5:10'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (5, 10, 1)


    def test_multiple_ranges(self):
        self.setup_spec(specs_strings=['3:30', '4:40'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 2
        assert self.flatten_spec(0) == (3, 30, 1)
        assert self.flatten_spec(1) == (4, 40, 1)


    def test_stepping(self):
        self.setup_spec(specs_strings=['5:10:1'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (5, 10, 1)

        self.setup_spec(specs_strings=['5:10:2'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (5, 10, 2)

        self.setup_spec(specs_strings=['::2'], spec_type='incl_rec')
        assert self.flatten_spec(0) == (0, 100, 2)


    def test_negative_range(self):
        self.setup_spec(specs_strings=['-10:-2'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (90, 98, 1)


    def test_out_of_range_negative_skipping(self):
        self.setup_spec(specs_strings=['20:10:-1'], item_count=None)
        assert self.flatten_spec(0) == (20, 10, -1)


    def test_negative_skipping(self):
        self.setup_spec(specs_strings=['8:2:-1'], spec_type='incl_rec')
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (8, 2, -1)


    def test_minusone_item_count_with_empty_stop(self):
        self.setup_spec(specs_strings=['2::'], item_count=None)
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (2, sys.maxsize, 1)


    def test_minusone_item_count_with_empty_stop_and_neg_step(self):
        self.setup_spec(specs_strings=['2::-1'], item_count=None)
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (2, 0,  -1.0)


    def test_minusone_item_count_with_empty_start_and_neg_step(self):
        with pytest.raises(mod.NegativeStepWithoutItemCountError):
            self.setup_spec(specs_strings=['::-1'], item_count=None)


    def test_minusone_item_count_with_empty_start_and_pos_step(self):
        self.setup_spec(specs_strings=['::1'], item_count=None)
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (0, sys.maxsize, 1)

    def test_good_item_count_with_empty_start_and_pos_step(self):
        self.setup_spec(specs_strings=['::-1'], item_count=100)
        assert len(self.spec.specs_final) == 1
        assert self.flatten_spec(0) == (100, 0, -1)



class TestIndexer(object):

    def setup_spec(self,
                   specs_strings,
                   spec_type='incl_rec',
                   item_count=sys.maxsize,
                   item_max=mod.MAX_INDEX_REC_CNT):

        item_count = 100

        self.spec = mod.Specifications(spec_type=spec_type,
                                       specs_strings=specs_strings,
                                       header=None,
                                       infile_item_count=item_count)

        self.indexer = mod.Indexer(self.spec.specs_final)
        self.indexer._item_max = item_max
        self.indexer.builder()
        self.index = self.indexer.index


    def test_index_too_big(self):
        self.setup_spec(['1', '2', '3', '4', '5', '6', '7'], item_max=3)
        assert self.indexer.index == []
        assert self.indexer.valid is False

        self.setup_spec(['1', '2', '3'], item_max=3)
        assert self.indexer.index == [1, 2, 3]
        assert self.indexer.valid is True

        self.setup_spec(['1', '2', '3'], item_max=2)
        assert self.indexer.index == []
        assert self.indexer.valid is False

        self.setup_spec(['1:999'], item_max=5)
        assert self.index == []
        assert self.indexer.valid is False


    def test_singles(self):
        self.setup_spec(['1', '2', '3'])
        assert self.index == [1, 2, 3]


    def test_ranges(self):
        self.setup_spec(['1:3', '20:23', '30:33'])
        assert self.index == [1, 2, 20, 21, 22, 30, 31, 32]


    def test_out_of_order_singles(self):
        self.setup_spec(['1', '3', '2'])
        assert self.index == [1, 3, 2]


    def test_with_negatives(self):
        self.setup_spec(['1', '-3', '2'])
        assert self.index == [1, 97, 2]


    def test_stepping(self):
        self.setup_spec(['1:8:2'])
        assert self.index == [1, 3, 5, 7]


    def test_negative_stepping(self):
        self.setup_spec(['8:1:-1'])
        assert self.index == [8, 7, 6, 5, 4, 3, 2]


    def test_unbounded_ends(self):
        self.setup_spec(['95:'])
        assert self.index == [95, 96, 97, 98, 99]

        self.setup_spec([':5'])
        assert self.index == [0, 1, 2, 3, 4]


    def test_empty(self):
        self.setup_spec([])
        assert self.index == []


    def test_repeats(self):
        self.setup_spec(['1', '2', '2'])
        assert self.index == [1, 2, 2]




class TestSpecProcessor(object):

    def runner(self,
                      spec_strings,
                      loc,
                      spec_type='incl_rec',
                      item_count=4,
                      header=None):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """

        if header:
           header_obj = csvhelper.Header()
           header_obj.load_from_list(field_names=header)
        else:
           header_obj = None

        self.specs = mod.Specifications(spec_type,
                                        specs_strings=spec_strings,
                                        header=header_obj,
                                        infile_item_count=item_count)


    def test_invalid_data_without_header(self):

        # missing colon:
        with pytest.raises(mod.UnidentifiableNonNumericSpec):
            self.runner(['2 5'], loc=0, item_count=80)

        # extra colon:
        with pytest.raises(SystemExit):
            self.runner(['2:5:1:6'], loc=0, item_count=80)


        # test a starting number larger than ending:
        with pytest.raises(SystemExit):
            self.runner(['5:2'], loc=0, item_count=80)
            self.sp = mod.SpecProcessor(self.specs)

        # column names, but no header:
        with pytest.raises(mod.UnidentifiableNonNumericSpec):
            self.runner(['account_id'], loc=0, item_count=80)


    def test_header_with_name_but_no_header(self):
        with pytest.raises(mod.UnidentifiableNonNumericSpec):
            self.runner(['account_id'], loc=0, item_count=80)

    def test_header_with_a_name(self):
        self.runner(['account_id'],
                    loc=0,
                    item_count=80,
                    header=['account_id', 'cust_id', 'zip'])
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.index == [0]

    def test_header_with_name_range(self):
        self.runner(['account_id:zip'],
                           loc=0,
                           item_count=80,
                           header=['account_id', 'cust_id', 'zip'])
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.index == [0, 1]

    def test_header_with_name_range_and_spaces(self):
        self.runner(['account_id : zip'],
                           loc=0,
                           item_count=80,
                           header=['account_id', 'cust_id', 'zip'])
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.index == [0, 1]


    def test_header_with_nonmatching_name(self):
        with pytest.raises(SystemExit):
            self.runner(['gorilla'],
                            loc=0,
                            item_count=80,
                            header=['account_id', 'cust_id', 'zip'])
            self.sp = mod.SpecProcessor(self.specs)



class TestSpecProcessorItemEvaluator(object):

    def runner(self,
               spec_strings,
               loc,
               spec_type='incl_rec',
               item_count=80,
               header=None):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """
        if header:
           header_obj = csvhelper.Header()
           header_obj.load_from_list(field_names=header)
        else:
           header_obj = None

        self.specs = mod.Specifications(spec_type,
                                        specs_strings=spec_strings,
                                        header=header_obj,
                                        infile_item_count=item_count)


    def test_all_conditions(self):
        self.runner(['account_id'],
                    loc=0,
                    item_count=80,
                    header=['account_id', 'cust_id', 'zip'])

        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.index == [0]

        # Single Cols
        specs = mod.Specifications(spec_type='incl_rec',
                                   specs_strings=['5'],
                                   infile_item_count=80)
        assert self.sp._spec_item_check(specs.specs_final[0], 5)

        # Ranges:
        specs = mod.Specifications(spec_type='incl_rec',
                                   specs_strings=['5:10:1'])
        assert self.sp._spec_item_check(specs.specs_final[0], 5)
        assert self.sp._spec_item_check(specs.specs_final[0], 9)
        assert self.sp._spec_item_check(specs.specs_final[0], 10) is False



class TestSpecProcessorEvaluator(object):


    def runner(self,
               spec_strings,
               spec_type='incl_rec',
               item_count=80,
               header=None):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """
        if header:
            header_obj = csvhelper.Header()
            header_obj.load_from_list(field_names=header)
        else:
            header_obj = None

        self.specs = mod.Specifications(spec_type,
                                        specs_strings=spec_strings,
                                        header=header_obj,
                                        infile_item_count=item_count)


    def test_evaluate_positive_specs(self):

        self.runner(['5', '7', '10:16'],
                    item_count=80)

        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.index == [5, 7, 10, 11, 12, 13, 14, 15]

        assert self.sp.specs_evaluator(5) is True
        assert self.sp.specs_evaluator(50) is False

        assert self.sp.specs_evaluator(13) is True


    def test_evaluate_all(self):

        self.runner([':'],
                    item_count=80)
        self.sp = mod.SpecProcessor(self.specs)

        assert self.sp.specs_evaluator(5) is True
        assert self.sp.specs_evaluator(7) is True

        # The following test is being deactivated since the SpecProcessor depends
        # on the calling code to only provide valid locations:
        #assert self.sp.specs_evaluator(150) is False


    def test_evaluate_negative_specs(self):
        self.runner([':-60'],
                    item_count=80)
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.specs_evaluator(7) is True
        assert self.sp.specs_evaluator(33) is False

        self.runner(['-60:-40'],
                    item_count=80)
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.specs_evaluator(7) is False
        assert self.sp.specs_evaluator(25) is True
        assert self.sp.specs_evaluator(78) is False

        self.runner(['10', '50:-10'],
                    item_count=80)
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.specs_evaluator(10)
        assert self.sp.specs_evaluator(5) is False
        assert self.sp.specs_evaluator(50)
        assert self.sp.specs_evaluator(69)
        assert self.sp.specs_evaluator(79) is False

        self.runner(['10:-1'],
                    item_count=80)
        self.sp = mod.SpecProcessor(self.specs)
        assert self.sp.specs_evaluator(5) is False
        assert self.sp.specs_evaluator(10)
        assert self.sp.specs_evaluator(78)
        assert self.sp.specs_evaluator(79) is False
        assert self.sp.specs_evaluator(80) is False



class TestAgainstPythonSliceDocs(object):
    """ From Python tutorial:
        One way to remember how slices work is to think of the indices as
        pointing between characters, with the left edge of the first character
        numbered 0. Then the right edge of the last character of a string of n
        characters has index n, for example:
        +---+---+---+---+---+
        | a | b | c | d | e |
        +---+---+---+---+---+
        0   1   2   3   4   5
       -5  -4  -3  -2  -1
       The first row of numbers gives the position of the indices 0...5 in the
       string; the second row gives the corresponding negative indices. The
       slice from i to j consists of all characters between the edges labeled i
       and j, respectively.
    """

    def simple_runner(self,
                      spec_strings,
                      loc,
                      spec_type='incl_rec',
                      item_count=4,
                      header=None):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """
        specifications = mod.Specifications(spec_type,
                                            specs_strings=spec_strings,
                                            header=header,
                                            infile_item_count=item_count)
        self.sp = mod.SpecProcessor(specifications)
        return self.sp.specs_evaluator(loc)


    def test_evaluate_python_doc_example_1(self):
        # a[start:end] # items start through end-1
        # >>> a = 'abcde'
        # >>> a[1:3]
        # 'bc'
        assert self.simple_runner(['1:3'], loc=0) is False
        assert self.simple_runner(['1:3'], loc=1)
        assert self.simple_runner(['1:3'], loc=2)
        assert self.simple_runner(['1:3'], loc=3) is False
        assert self.simple_runner(['1:3'], loc=4) is False

    def test_evaluate_python_doc_example_2(self):
        # a[start:]    # items start through the rest of the array
        # >>> a = 'abcde'
        # >>> a[2:]
        # 'cde'
        assert self.simple_runner(['2:'], loc=0) is False
        assert self.simple_runner(['2:'], loc=1) is False
        assert self.simple_runner(['2:'], loc=2)
        assert self.simple_runner(['2:'], loc=3)
        assert self.simple_runner(['2:'], loc=4) is False

    def test_evaluate_python_doc_example_3(self):
        # a[:end]      # items from the beginning through end-1
        # >>> a = 'abcde'
        # >>> a[:3]
        # 'abc'
        assert self.simple_runner([':3'], loc=0)
        assert self.simple_runner([':3'], loc=1)
        assert self.simple_runner([':3'], loc=2)
        assert self.simple_runner([':3'], loc=3) is False
        assert self.simple_runner([':3'], loc=4) is False

    def test_evaluate_python_doc_example_4(self):
        # a[:]         # a copy of the whole array
        # >>> a = 'abcde'
        # >>> a[:]
        # 'abcde'
        assert self.simple_runner([':'], loc=0)
        assert self.simple_runner([':'], loc=1)
        assert self.simple_runner([':'], loc=2)
        assert self.simple_runner([':'], loc=3)
        assert self.simple_runner([':'], loc=4)

    def test_evaluate_python_doc_example_5(self):
        # a[-1]    # last item in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'e'
        assert self.simple_runner(['-1'], loc=0) is False
        assert self.simple_runner(['-1'], loc=1) is False
        assert self.simple_runner(['-1'], loc=2) is False
        assert self.simple_runner(['-1'], loc=3)
        assert self.simple_runner(['-1'], loc=4) is False

    def test_evaluate_python_doc_example_6(self):
        # a[-2:]   # last two items in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'de'
        assert self.simple_runner(['-2:'], loc=0) is False
        assert self.simple_runner(['-2:'], loc=1) is False
        assert self.simple_runner(['-2:'], loc=2)
        assert self.simple_runner(['-2:'], loc=3)
        assert self.simple_runner(['-2:'], loc=4) is False

    def test_evaluate_python_doc_example_7(self):
        # a[:-2]   # everything except the last two items
        # >>> a = 'abcde'
        # >>> a[:-2]
        # 'abc'
        assert self.simple_runner([':-2'], loc=0)
        assert self.simple_runner([':-2'], loc=1)
        assert self.simple_runner([':-2'], loc=2) is False
        assert self.simple_runner([':-2'], loc=3) is False
        assert self.simple_runner([':-2'], loc=4) is False

    def test_evaluate_python_doc_example_8(self):
        # a[1:100] # everything frm the second item to the end - up to the 100th
        # >>> a = 'abcde'
        # >>> a[1:100]
        # 'bcde'
        assert self.simple_runner(['1:100'], loc=0) is False
        assert self.simple_runner(['1:100'], loc=1)
        assert self.simple_runner(['1:100'], loc=2)
        assert self.simple_runner(['1:100'], loc=3)
        assert self.simple_runner(['1:100'], loc=4)

    def test_evaluate_python_doc_example_9(self):
        # >>> a = 'abcde'
        # >>> a[0]      # (since -0 equals 0)
        # 'a'
        # >>> a[-0]     # (since -0 equals 0)
        # 'a'
        assert self.simple_runner(['0'], loc=0)
        assert self.simple_runner(['0'], loc=1) is False
        assert self.simple_runner(['0'], loc=2) is False
        assert self.simple_runner(['0'], loc=3) is False
        assert self.simple_runner(['0'], loc=4) is False
        assert self.simple_runner(['-0'], loc=0)
        assert self.simple_runner(['0'], loc=1) is False
        assert self.simple_runner(['0'], loc=2) is False
        assert self.simple_runner(['0'], loc=3) is False
        assert self.simple_runner(['0'], loc=4) is False

    def test_evaluate_python_doc_example_10(self):
        # >>> a = 'abcde'
        # >>> a[-100:]  # excessive negatives are truncated - in ranges
        # 'abcde'
        assert self.simple_runner(['-100:'], loc=0)
        assert self.simple_runner(['-100:'], loc=1)
        assert self.simple_runner(['-100:'], loc=2)
        assert self.simple_runner(['-100:'], loc=3)
        assert self.simple_runner(['-100:'], loc=4) is False

    def test_evaluate_python_doc_example_11(self):
        # >>> a = 'abcde'
        # >>> a[-100]       # out of range references == Exception!
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        # It's different because we don't want to pay the cost of counting
        # all the rows all the time
        assert self.simple_runner(['-100'], loc=0) is False
        assert self.simple_runner(['-100'], loc=1) is False
        assert self.simple_runner(['-100'], loc=2) is False
        assert self.simple_runner(['-100'], loc=3) is False
        assert self.simple_runner(['-100'], loc=4) is False

    def test_evaluate_python_doc_example_12(self):
        # >>> a = 'abcde'
        # >>> a[10]         # out of range references == False
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        # It's different because we don't want to pay the cost of counting
        # all the rows all the time
        assert self.simple_runner(['10'], loc=0) is False
        assert self.simple_runner(['10'], loc=1) is False
        assert self.simple_runner(['10'], loc=2) is False
        assert self.simple_runner(['10'], loc=3) is False
        assert self.simple_runner(['10'], loc=4) is False
