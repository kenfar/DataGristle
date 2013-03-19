#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import functools
#import test_tools
try:
    import unittest2 as unittest
except ImportError:
    import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.location_slicer  as mod


#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(unittest.makeSuite(TestIsNegativeSpec))
#    suite.addTest(unittest.makeSuite(TestSpecProcessorValidator))
#    suite.addTest(unittest.makeSuite(TestSpecProcessorAdjuster))
#    suite.addTest(unittest.makeSuite(TestSpecProcessorItemEvaluator))
#    suite.addTest(unittest.makeSuite(TestSpecProcessorEvaluator))
#    suite.addTest(unittest.makeSuite(TestAgainstPythonSliceDocs))
#    unittest.TextTestRunner(verbosity=2).run(suite)
#
#    return suite



class TestIsNegativeSpec(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_is_negative_spec_simple_inputs(self):
        self.assertFalse(mod.is_negative_spec(['1']))
        self.assertFalse(mod.is_negative_spec(['1'],['1']))
        self.assertTrue(mod.is_negative_spec(['1'],['1'],['2'],['-12']))
        self.assertTrue(mod.is_negative_spec(['-1'],['1'],['2'],['-12']))
        self.assertFalse(mod.is_negative_spec(['0'],['1'],['2'],['3']))

    def test_is_negative_spec_complex_inputs(self):
        self.assertFalse(mod.is_negative_spec(['1','2'],['1'],['2'],['2']))
        self.assertFalse(mod.is_negative_spec([':'],['1'],['2'],['2']))
        self.assertFalse(mod.is_negative_spec(['1:'],['1'],['2'],['2']))
        self.assertFalse(mod.is_negative_spec([':1'],['1'],['2'],['2']))
        self.assertFalse(mod.is_negative_spec(['1:1'],['1'],['2'],['2']))
        self.assertFalse(mod.is_negative_spec(['1','5:'],['1'],['2'],['2']))
        self.assertTrue(mod.is_negative_spec(['-1:'],['1'],['2'],['2']))
        self.assertTrue(mod.is_negative_spec([':-1'],['1'],['2'],['2']))
        self.assertTrue(mod.is_negative_spec(['-1:-1'],['1'],['2'],['2']))
        self.assertTrue(mod.is_negative_spec(['-1:-1', '3:9'],['1'],['2'],['2']))

    def test_is_negative_spec_none_values(self):
        self.assertFalse(mod.is_negative_spec(['1'], None))
        self.assertFalse(mod.is_negative_spec(None))



class TestSpecProcessorValidator(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_spec_validation(self):
        self.failUnlessRaises(ValueError, mod.SpecProcessor, '3', 'bad spec')
        self.failUnlessRaises(ValueError, mod.SpecProcessor, '3', 'bad spec')

    def test_negative_check(self):
        # check simplest spec
        self.spec_processor = mod.SpecProcessor(['3'], 'rec_incl_spec')
        self.assertFalse(self.spec_processor.has_negatives)

        # check more complex spec
        sp2 = mod.SpecProcessor(['3:5','0','18:',':'], 'rec_incl_spec')
        self.assertFalse(sp2.has_negatives)

        # check negative spec
        sp2 = mod.SpecProcessor(['3:5'], 'rec_incl_spec')
        sp3 = mod.SpecProcessor(['-1'], 'rec_incl_spec')
        self.assertTrue(sp3.has_negatives)

    def test_spec_evaluator(self):
        sp4 = mod.SpecProcessor(['3:5'], 'rec_incl_spec')
        #self.assertTrue(sp4.spec_evaluator(3

    def test_spec_validator(self):
        sp5 = mod.SpecProcessor(['3:5'], 'rec_incl_spec')
        self.assertTrue(sp5._spec_validator(['3']))
        self.assertTrue(sp5._spec_validator(['3:8']))
        self.assertTrue(sp5._spec_validator([':']))
        self.assertTrue(sp5._spec_validator(['3:5','7','10:',':',':19']))
        self.assertRaises(ValueError, sp5._spec_validator, [''])
        self.assertRaises(ValueError, sp5._spec_validator, 'a')
        self.assertRaises(ValueError, sp5._spec_validator, ['a'])
        self.assertRaises(ValueError, sp5._spec_validator, ['-'])
        self.assertRaises(ValueError, sp5._spec_validator, [''])
        self.assertRaises(ValueError, sp5._spec_validator, ['5:1'])
        self.assertRaises(ValueError, sp5._spec_validator, ['1:10:20'])



class TestSpecProcessorAdjuster(unittest.TestCase):
    def setUp(self):
        self.sp = mod.SpecProcessor(['3'], 'rec_inc_spec')
    def tearDown(self):
        pass
    def test_adjust_one_spec(self):

        self.sp = mod.SpecProcessor(['5'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.sp.spec_adjuster()
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)

        self.sp = mod.SpecProcessor(['5:15'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)

        self.sp = mod.SpecProcessor(['5:9','10:'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)

        self.sp = mod.SpecProcessor([':'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)

        self.sp = mod.SpecProcessor(['-1'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, ['80'])

        self.sp = mod.SpecProcessor(['-20:-10'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=80)
        self.assertEqual(self.sp.adj_spec, ['61:71'])

        self.sp = mod.SpecProcessor(['-100:'], 'rec_inc_spec')
        self.sp.spec_adjuster(loc_max=1234567890)
        self.assertEqual(self.sp.adj_spec, ['1234567791:'])



class TestSpecProcessorItemEvaluator(unittest.TestCase):
    def setUp(self):
        self.sp = mod.SpecProcessor([':'], 'foo')
    def tearDown(self):
        pass

    def test_a(self):
        self.assertTrue(self.sp._spec_item_evaluator(':',     10))
        self.assertTrue(self.sp._spec_item_evaluator('10',    10))
        self.assertTrue(self.sp._spec_item_evaluator('1:100', 10))
        self.assertTrue(self.sp._spec_item_evaluator('1:',    10))
        self.assertTrue(self.sp._spec_item_evaluator('10:',   10))
        self.assertTrue(self.sp._spec_item_evaluator(':100',  10))
        self.assertTrue(self.sp._spec_item_evaluator(':11',   10))
        self.assertFalse(self.sp._spec_item_evaluator('',     10))
        self.assertFalse(self.sp._spec_item_evaluator('1',    10))
        self.assertFalse(self.sp._spec_item_evaluator('1:5',  10))
        self.assertFalse(self.sp._spec_item_evaluator('11:',  10))
        self.assertFalse(self.sp._spec_item_evaluator(':10',  10))


class TestSpecProcessorEvaluator(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def simple_setup(self, spec, spec_name, loc_max):
        self.sp = mod.SpecProcessor(spec, spec_name)
        self.sp.spec_adjuster(loc_max)

    def test_evaluate_positive_specs(self):

        self.simple_setup(['5'], 'rec_incl_spec', 80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.assertTrue(self.sp.spec_evaluator(5))
        self.assertFalse(self.sp.spec_evaluator(8))

        self.simple_setup(['5','15'], 'rec_incl_spec', 80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.assertTrue(self.sp.spec_evaluator(5))
        self.assertFalse(self.sp.spec_evaluator(33))

        self.simple_setup(['5:10','15'], 'rec_incl_spec', 80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.assertTrue(self.sp.spec_evaluator(7))
        self.assertFalse(self.sp.spec_evaluator(33))

        self.simple_setup([':'], 'rec_incl_spec', 80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.assertTrue(self.sp.spec_evaluator(7))

        self.simple_setup(['50:','15'], 'rec_incl_spec', 80)
        self.assertEqual(self.sp.adj_spec, self.sp.orig_spec)
        self.assertTrue(self.sp.spec_evaluator(76))
        self.assertTrue(self.sp.spec_evaluator(15))
        self.assertFalse(self.sp.spec_evaluator(33))


    def test_evaluate_negative_specs(self):
        self.simple_setup([':-60'], 'rec_incl_spec', 80)
        self.assertTrue(self.sp.spec_evaluator(7))
        self.assertFalse(self.sp.spec_evaluator(33))

        self.simple_setup(['-60:-40'], 'rec_incl_spec', 80)
        self.assertFalse(self.sp.spec_evaluator(7))
        self.assertTrue(self.sp.spec_evaluator(25))
        self.assertFalse(self.sp.spec_evaluator(79))

        self.simple_setup(['10','50:-10'], 'rec_incl_spec', 80)
        self.assertTrue(self.sp.spec_evaluator(10))
        self.assertFalse(self.sp.spec_evaluator(5))
        self.assertTrue(self.sp.spec_evaluator(50))
        self.assertTrue(self.sp.spec_evaluator(69))
        self.assertFalse(self.sp.spec_evaluator(79))

        self.simple_setup(['10:-1'], 'rec_incl_spec', 80)
        self.assertFalse(self.sp.spec_evaluator(5))
        self.assertTrue(self.sp.spec_evaluator(10))
        self.assertTrue(self.sp.spec_evaluator(78))
        self.assertTrue(self.sp.spec_evaluator(79))
        self.assertFalse(self.sp.spec_evaluator(80))


    def test_evaluate_many_items(self):
        self.simple_setup(['1','5','10','15','20:30','35'], 'rec_incl_spec', 80)
        self.assertTrue(self.sp.spec_evaluator(5))
        self.assertFalse(self.sp.spec_evaluator(7))
        self.assertTrue(self.sp.spec_evaluator(27))
        self.assertFalse(self.sp.spec_evaluator(50))

class TestAgainstPythonSliceDocs(unittest.TestCase):
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
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def simple_runner(self, spec, loc):
        """ Creates the Spec Processor object with default settings for the
            specification and record length.
        """
        spec_name = 'foo'
        loc_max   = 4     # max length - based on 0 offset

        self.sp = mod.SpecProcessor(spec, spec_name)
        self.sp.spec_adjuster(loc_max)
        return self.sp.spec_evaluator(loc)


    def test_evaluate_python_doc_example_1(self):
        # a[start:end] # items start through end-1
        # >>> a = 'abcde'
        # >>> a[1:3]
        # 'bc'
        self.assertFalse(self.simple_runner(['1:3'], 0))
        self.assertTrue(self.simple_runner(['1:3'],  1))
        self.assertTrue(self.simple_runner(['1:3'],  2))
        self.assertFalse(self.simple_runner(['1:3'], 3))
        self.assertFalse(self.simple_runner(['1:3'], 4))

    def test_evaluate_python_doc_example_2(self):
        # a[start:]    # items start through the rest of the array
        # >>> a = 'abcde'
        # >>> a[2:]
        # 'cde'
        self.assertFalse(self.simple_runner(['2:'], 0))
        self.assertFalse(self.simple_runner(['2:'], 1))
        self.assertTrue(self.simple_runner(['2:'],  2))
        self.assertTrue(self.simple_runner(['2:'],  3))
        self.assertTrue(self.simple_runner(['2:'],  4))

    def test_evaluate_python_doc_example_3(self):
        # a[:end]      # items from the beginning through end-1
        # >>> a = 'abcde'
        # >>> a[:3]
        # 'abc'
        self.assertTrue(self.simple_runner([':3'],  0))
        self.assertTrue(self.simple_runner([':3'],  1))
        self.assertTrue(self.simple_runner([':3'],  2))
        self.assertFalse(self.simple_runner([':3'], 3))
        self.assertFalse(self.simple_runner([':3'], 4))

    def test_evaluate_python_doc_example_4(self):
        # a[:]         # a copy of the whole array
        # >>> a = 'abcde'
        # >>> a[:]
        # 'abcde'
        self.assertTrue(self.simple_runner([':'],  0))
        self.assertTrue(self.simple_runner([':'],  1))
        self.assertTrue(self.simple_runner([':'],  2))
        self.assertTrue(self.simple_runner([':'],  3))
        self.assertTrue(self.simple_runner([':'],  4))



    def test_evaluate_python_doc_example_5(self):
        # a[-1]    # last item in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'e'
        self.assertFalse(self.simple_runner(['-1'],  0))
        self.assertFalse(self.simple_runner(['-1'],  1))
        self.assertFalse(self.simple_runner(['-1'],  2))
        self.assertFalse(self.simple_runner(['-1'],  3))
        self.assertTrue(self.simple_runner(['-1'],   4))

    def test_evaluate_python_doc_example_6(self):
        # a[-2:]   # last two items in the array
        # >>> a = 'abcde'
        # >>> a[-1]
        # 'de'
        self.assertFalse(self.simple_runner(['-2:'],  0))
        self.assertFalse(self.simple_runner(['-2:'],  1))
        self.assertFalse(self.simple_runner(['-2:'],  2))
        self.assertTrue(self.simple_runner(['-2:'],   3))
        self.assertTrue(self.simple_runner(['-2:'],   4))

    def test_evaluate_python_doc_example_7(self):
        # a[:-2]   # everything except the last two items
        # >>> a = 'abcde'
        # >>> a[:-2]
        # 'abc'
        self.assertTrue(self.simple_runner([':-2'],  0))
        self.assertTrue(self.simple_runner([':-2'],  1))
        self.assertTrue(self.simple_runner([':-2'],  2))
        self.assertFalse(self.simple_runner([':-2'],   3))
        self.assertFalse(self.simple_runner([':-2'],   4))

    def test_evaluate_python_doc_example_8(self):
        # a[1:100] # everything frm the second item to the end - up to the 100th
        # >>> a = 'abcde'
        # >>> a[1:100]
        # 'bcde'
        self.assertFalse(self.simple_runner(['1:100'],  0))
        self.assertTrue(self.simple_runner(['1:100'],   1))
        self.assertTrue(self.simple_runner(['1:100'],   2))
        self.assertTrue(self.simple_runner(['1:100'],   3))
        self.assertTrue(self.simple_runner(['1:100'],   4))

    def test_evaluate_python_doc_example_9(self):
        # >>> a = 'abcde'
        # >>> a[0]      # (since -0 equals 0)
        # 'a'
        # >>> a[-0]     # (since -0 equals 0)
        # 'a'
        self.assertTrue(self.simple_runner(['0'],        0))
        self.assertFalse(self.simple_runner(['0'],       1))
        self.assertFalse(self.simple_runner(['0'],       2))
        self.assertFalse(self.simple_runner(['0'],       3))
        self.assertFalse(self.simple_runner(['0'],       4))
        self.assertTrue(self.simple_runner(['-0'],       0))
        self.assertFalse(self.simple_runner(['0'],       1))
        self.assertFalse(self.simple_runner(['0'],       2))
        self.assertFalse(self.simple_runner(['0'],       3))
        self.assertFalse(self.simple_runner(['0'],       4))

    def test_evaluate_python_doc_example_10(self):
        # >>> a = 'abcde'
        # >>> a[-100:]  # excessive negatives are truncated - in ranges
        # 'abcde'
        self.assertTrue(self.simple_runner(['-100:'],    0))
        self.assertTrue(self.simple_runner(['-100:'],    1))
        self.assertTrue(self.simple_runner(['-100:'],    2))
        self.assertTrue(self.simple_runner(['-100:'],    3))
        self.assertTrue(self.simple_runner(['-100:'],    4))

    def test_evaluate_python_doc_example_11(self):
        # >>> a = 'abcde'
        # >>> a[-100]       # out of range references == False
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        self.assertFalse(self.simple_runner(['-100'],    0))
        self.assertFalse(self.simple_runner(['-100'],    1))
        self.assertFalse(self.simple_runner(['-100'],    2))
        self.assertFalse(self.simple_runner(['-100'],    3))
        self.assertFalse(self.simple_runner(['-100'],    4))

    def test_evaluate_python_doc_example_12(self):
        # >>> a = 'abcde'
        # >>> a[10]         # out of range references == False
        # IndexError
        # Here GristleSlicer is different than Python - and returns a false
        # rather than an exception
        self.assertFalse(self.simple_runner(['10'],      0))
        self.assertFalse(self.simple_runner(['10'],      1))
        self.assertFalse(self.simple_runner(['10'],      2))
        self.assertFalse(self.simple_runner(['10'],      3))
        self.assertFalse(self.simple_runner(['10'],      4))

#if __name__ == "__main__":
#    unittest.main(suite())


















