#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
from pprint import pprint as pp

import pytest

import datagristle.location_slicer  as mod


class TestIsNegativeSpec(object):

    def test_has_negatives_simple_inputs(self):

        assert mod.spec_has_negatives(['1']) is False

        assert mod.spec_has_negatives(['1', '1']) is False

        assert mod.spec_has_negatives(['-1', '1', '2', '-12'])

        assert mod.spec_has_negatives(['0', '1', '2', '3']) is False


    def test_has_negatives_complex_inputs(self):

        assert mod.spec_has_negatives(['1', '2']) is False

        assert mod.spec_has_negatives([':', '1', '2']) is False

        assert mod.spec_has_negatives(['1:', '1', '2']) is False

        assert mod.spec_has_negatives([':1', '1', '2']) is False

        assert mod.spec_has_negatives(['1:1', '1', '2']) is False

        assert mod.spec_has_negatives(['1', '1:', '2']) is False

        assert mod.spec_has_negatives(['-1:', '2'])

        assert mod.spec_has_negatives([':-1', '2'])

        assert mod.spec_has_negatives(['-1:-1', '2'])

        assert mod.spec_has_negatives(['-1:-1', '3:9'])


    def test_has_negatives_none_values(self):

        assert mod.spec_has_negatives([]) is False



class TestSpecProcessorValidator(object):

    def test_spec_validation(self):

        # pylint: disable=E1101
        with pytest.raises(ValueError):
            mod.SpecProcessor('3', header=None, infile_item_count=10)
        with pytest.raises(ValueError):
            mod.SpecProcessor('3', header=None, infile_item_count=10)
        # pylint: enable=E1101

#    def test_negative_check(self):
#        # check simplest spec
#        self.spec_processor = mod.SpecProcessor(['3'], 'rec_incl_spec', header=None, infiles=None, infile_item_count=10)
#        assert self.spec_processor.has_negatives() is False
#
#        # check more complex spec
#        sp2 = mod.SpecProcessor(['3:5', '0', '18:', ':'], 'rec_incl_spec')
#        assert sp2.has_negatives() is False
#
#        # check negative spec
#        sp2 = mod.SpecProcessor(['3:5'], 'rec_incl_spec')
#        sp3 = mod.SpecProcessor(['-1'], 'rec_incl_spec')
#        assert sp3.has_negatives()
#

    def test_spec_validator(self):
        sp5 = mod.SpecProcessor(['3:5'], header=None, infile_item_count=10)
        assert sp5._spec_validator(['3'])
        assert sp5._spec_validator(['3:8'])
        assert sp5._spec_validator([':'])
        assert sp5._spec_validator(['3:5', '7', '10:', ':', ':19'])
        # pylint: disable=E1101
        with pytest.raises(ValueError):
            sp5._spec_validator([''])
        with pytest.raises(ValueError):
            sp5._spec_validator('a')
        with pytest.raises(ValueError):
            sp5._spec_validator(['a'])
        with pytest.raises(ValueError):
            sp5._spec_validator(['-'])
        with pytest.raises(ValueError):
            sp5._spec_validator([''])
        with pytest.raises(ValueError):
            sp5._spec_validator(['5:1'])
        with pytest.raises(ValueError):
            sp5._spec_validator(['1:10:20'])
        # pylint: enable=E1101



class TestSpecProcessorNegativeTranslator(object):

#    def setup_method(self, method):
#        self.sp = mod.SpecProcessor(['3'], 'rec_inc_spec')

    def test_adjust_one_spec(self):
        header = None
        infiles = None
        infile_item_count = 80

        # test a single positive:
        self.sp = mod.SpecProcessor(['5'], header, infile_item_count)
        #self.sp._spec_negative_translator(loc_max=80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        #self.sp._spec_negative_translator(loc_max=80)
        #assert self.sp.positive_spec == self.sp.numeric_spec

        # test a range of positives:
        self.sp = mod.SpecProcessor(['5:15'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count=80)
        pp(self.sp.numeric_specs)
        pp(self.sp.positive_specs)
        assert self.sp.positive_specs == self.sp.numeric_specs

        # test a couple of ranges, one unbound:
        self.sp = mod.SpecProcessor(['5:9', '10:'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count=80)
        assert self.sp.positive_specs == self.sp.numeric_specs

        # test a single range with both sides unbounded:
        self.sp = mod.SpecProcessor([':'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count=80)
        assert self.sp.positive_specs == self.sp.numeric_specs

        # test a single negative:
        self.sp = mod.SpecProcessor(['-1'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count=80)
        assert self.sp.positive_specs == ['80']

        # test a range of negatives:
        self.sp = mod.SpecProcessor(['-20:-10'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count=80)
        assert self.sp.positive_specs == ['61:71']

        # test a range of negative and unbounded:
        infile_item_count=1234567890
        self.sp = mod.SpecProcessor(['-100:'], header, infile_item_count)
        self.sp._spec_negative_translator(infile_item_count)
        assert self.sp.positive_specs == ['1234567791:']



class TestSpecProcessorItemEvaluator(object):

    def setup_method(self, method):
        self.sp = mod.SpecProcessor([':'], header=None, infile_item_count=80)

    def test_a(self):
        assert self.sp._spec_item_evaluator(':', 10)
        assert self.sp._spec_item_evaluator('10', 10)
        assert self.sp._spec_item_evaluator('1:100', 10)
        assert self.sp._spec_item_evaluator('1:', 10)
        assert self.sp._spec_item_evaluator('10:', 10)
        assert self.sp._spec_item_evaluator(':100', 10)
        assert self.sp._spec_item_evaluator(':11', 10)
        assert self.sp._spec_item_evaluator('', 10) is False
        assert self.sp._spec_item_evaluator('1', 10) is False
        assert self.sp._spec_item_evaluator('1:5', 10) is False
        assert self.sp._spec_item_evaluator('11:', 10) is False
        assert self.sp._spec_item_evaluator(':10', 10) is False



class TestSpecProcessorEvaluator(object):

    def simple_setup(self, spec, spec_name, infile_item_count):
        self.sp = mod.SpecProcessor(spec, header=None, infile_item_count=infile_item_count)
        self.sp._spec_negative_translator(infile_item_count)

    def test_evaluate_starting_offsets(self):

        self.simple_setup(['0'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(0)
        assert self.sp.spec_evaluator(1) is False

    def test_evaluate_positive_specs(self):

        self.simple_setup(['5'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(5)
        assert self.sp.spec_evaluator(8) is False

        self.simple_setup(['5', '15'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(5)
        assert self.sp.spec_evaluator(33) is False

        self.simple_setup(['5:10', '15'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(7)
        assert self.sp.spec_evaluator(33) is False

        self.simple_setup([':'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(7)

        self.simple_setup(['50:', '15'], 'rec_incl_spec', 80)
        assert self.sp.positive_specs == self.sp.numeric_specs
        assert self.sp.spec_evaluator(76)
        assert self.sp.spec_evaluator(15)
        assert self.sp.spec_evaluator(33) is False


    def test_evaluate_negative_specs(self):
        self.simple_setup([':-60'], 'rec_incl_spec', 80)
        assert self.sp.spec_evaluator(7)
        assert self.sp.spec_evaluator(33) is False

        self.simple_setup(['-60:-40'], 'rec_incl_spec', 80)
        assert self.sp.spec_evaluator(7) is False
        assert self.sp.spec_evaluator(25)
        assert self.sp.spec_evaluator(78) is False

        self.simple_setup(['10', '50:-10'], 'rec_incl_spec', 80)
        assert self.sp.spec_evaluator(10)
        assert self.sp.spec_evaluator(5) is False
        assert self.sp.spec_evaluator(50)
        assert self.sp.spec_evaluator(69)
        assert self.sp.spec_evaluator(79) is False

        self.simple_setup(['10:-1'], 'rec_incl_spec', 80)
        assert self.sp.spec_evaluator(5) is False
        assert self.sp.spec_evaluator(10)
        assert self.sp.spec_evaluator(78)
        assert self.sp.spec_evaluator(79)
        assert self.sp.spec_evaluator(80) is False


    def test_evaluate_many_items(self):
        self.simple_setup(['1', '5', '10', '15', '20:30', '35'], 'rec_incl_spec', 80)
        assert self.sp.spec_evaluator(5)
        assert self.sp.spec_evaluator(7) is False
        assert self.sp.spec_evaluator(27)
        assert self.sp.spec_evaluator(50) is False



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

    def simple_runner(self, spec, loc):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """
        spec_name = 'foo'
        infile_item_count= 4     # max length - based on 0 offset

        self.sp = mod.SpecProcessor(spec, header=None, infile_item_count=infile_item_count)
        return self.sp.spec_evaluator(loc)


    def test_evaluate_python_doc_example_1(self):
        # a[start:end] # items start through end-1
        # >>> a = 'abcde'
        # >>> a[1:3]
        # 'bc'
        assert self.simple_runner(['1:3'], 0) is False
        assert self.simple_runner(['1:3'], 1)
        assert self.simple_runner(['1:3'], 2)
        assert self.simple_runner(['1:3'], 3) is False
        assert self.simple_runner(['1:3'], 4) is False

    def test_evaluate_python_doc_example_2(self):
        # a[start:]    # items start through the rest of the array
        # >>> a = 'abcde'
        # >>> a[2:]
        # 'cde'
        assert self.simple_runner(['2:'], 0) is False
        assert self.simple_runner(['2:'], 1) is False
        assert self.simple_runner(['2:'], 2)
        assert self.simple_runner(['2:'], 3)
        assert self.simple_runner(['2:'], 4)

    def test_evaluate_python_doc_example_3(self):
        # a[:end]      # items from the beginning through end-1
        # >>> a = 'abcde'
        # >>> a[:3]
        # 'abc'
        assert self.simple_runner([':3'], 0)
        assert self.simple_runner([':3'], 1)
        assert self.simple_runner([':3'], 2)
        assert self.simple_runner([':3'], 3) is False
        assert self.simple_runner([':3'], 4) is False

    def test_evaluate_python_doc_example_4(self):
        # a[:]         # a copy of the whole array
        # >>> a = 'abcde'
        # >>> a[:]
        # 'abcde'
        assert self.simple_runner([':'], 0)
        assert self.simple_runner([':'], 1)
        assert self.simple_runner([':'], 2)
        assert self.simple_runner([':'], 3)
        assert self.simple_runner([':'], 4)

    def test_evaluate_python_doc_example_5(self):
        # a[-1]    # last item in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'e'
        assert self.simple_runner(['-1'], 0) is False
        assert self.simple_runner(['-1'], 1) is False
        assert self.simple_runner(['-1'], 2) is False
        assert self.simple_runner(['-1'], 3) is False
        assert self.simple_runner(['-1'], 4)

    def test_evaluate_python_doc_example_6(self):
        # a[-2:]   # last two items in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'de'
        assert self.simple_runner(['-2:'], 0) is False
        assert self.simple_runner(['-2:'], 1) is False
        assert self.simple_runner(['-2:'], 2) is False
        assert self.simple_runner(['-2:'], 3)
        assert self.simple_runner(['-2:'], 4)

    def test_evaluate_python_doc_example_7(self):
        # a[:-2]   # everything except the last two items
        # >>> a = 'abcde'
        # >>> a[:-2]
        # 'abc'
        assert self.simple_runner([':-2'], 0)
        assert self.simple_runner([':-2'], 1)
        assert self.simple_runner([':-2'], 2)
        assert self.simple_runner([':-2'], 3) is False
        assert self.simple_runner([':-2'], 4) is False

    def test_evaluate_python_doc_example_8(self):
        # a[1:100] # everything frm the second item to the end - up to the 100th
        # >>> a = 'abcde'
        # >>> a[1:100]
        # 'bcde'
        assert self.simple_runner(['1:100'], 0) is False
        assert self.simple_runner(['1:100'], 1)
        assert self.simple_runner(['1:100'], 2)
        assert self.simple_runner(['1:100'], 3)
        assert self.simple_runner(['1:100'], 4)

    def test_evaluate_python_doc_example_9(self):
        # >>> a = 'abcde'
        # >>> a[0]      # (since -0 equals 0)
        # 'a'
        # >>> a[-0]     # (since -0 equals 0)
        # 'a'
        assert self.simple_runner(['0'], 0)
        assert self.simple_runner(['0'], 1) is False
        assert self.simple_runner(['0'], 2) is False
        assert self.simple_runner(['0'], 3) is False
        assert self.simple_runner(['0'], 4) is False
        assert self.simple_runner(['-0'], 0)
        assert self.simple_runner(['0'], 1) is False
        assert self.simple_runner(['0'], 2) is False
        assert self.simple_runner(['0'], 3) is False
        assert self.simple_runner(['0'], 4) is False

    def test_evaluate_python_doc_example_10(self):
        # >>> a = 'abcde'
        # >>> a[-100:]  # excessive negatives are truncated - in ranges
        # 'abcde'
        assert self.simple_runner(['-100:'], 0)
        assert self.simple_runner(['-100:'], 1)
        assert self.simple_runner(['-100:'], 2)
        assert self.simple_runner(['-100:'], 3)
        assert self.simple_runner(['-100:'], 4)

    def test_evaluate_python_doc_example_11(self):
        # >>> a = 'abcde'
        # >>> a[-100]       # out of range references == False
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        assert self.simple_runner(['-100'], 0) is False
        assert self.simple_runner(['-100'], 1) is False
        assert self.simple_runner(['-100'], 2) is False
        assert self.simple_runner(['-100'], 3) is False
        assert self.simple_runner(['-100'], 4) is False

    def test_evaluate_python_doc_example_12(self):
        # >>> a = 'abcde'
        # >>> a[10]         # out of range references == False
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        assert self.simple_runner(['10'], 0) is False
        assert self.simple_runner(['10'], 1) is False
        assert self.simple_runner(['10'], 2) is False
        assert self.simple_runner(['10'], 3) is False
        assert self.simple_runner(['10'], 4) is False
