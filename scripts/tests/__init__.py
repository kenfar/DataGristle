#!/usr/bin/env python

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_gristle_determinator_cmd    as determinator_cmd
import test_gristle_differ_cmd          as differ_cmd
import test_gristle_file_converter_cmd  as conv_cmd
import test_gristle_filter_cmd          as filter_cmd
import test_gristle_freaker             as freaker
import test_gristle_freaker_cmd         as freaker_cmd
import test_gristle_slicer_cmd          as slicer_cmd
import test_gristle_viewer_cmd          as viewer_cmd
import test_gristle_scalar_cmd          as scalar_cmd
import test_gristle_file_converter_cmd  as conv_cmd
import test_gristle_file_converter      as conv


def main():

    suite  = unittest.TestSuite()
    suite.addTest(determinator_cmd.suite())
    suite.addTest(differ_cmd.suite())
    suite.addTest(conv_cmd.suite())
    suite.addTest(filter_cmd.suite())
    suite.addTest(freaker.suite())
    suite.addTest(freaker_cmd.suite())
    suite.addTest(scalar_cmd.suite())
    suite.addTest(slicer_cmd.suite())
    suite.addTest(viewer_cmd.suite())
    suite.addTest(conv.suite())
    suite.addTest(conv_cmd.suite())
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()


