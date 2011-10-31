#!/usr/bin/env python

import os
import sys

import unittest
import test_gristle_differ_cmd          as differ_cmd
import test_gristle_file_converter_cmd  as conv_cmd
import test_gristle_filter_cmd          as filter_cmd
import test_gristle_slicer_cmd          as slicer_cmd
import test_gristle_slicer              as slicer
import test_gristle_viewer_cmd          as viewer_cmd
import test_gristle_determinator_cmd    as determinator_cmd


def main():

   suite  = unittest.TestSuite()
   suite.addTest(differ_cmd.suite())
   suite.addTest(conv_cmd.suite())
   suite.addTest(filter_cmd.suite())
   suite.addTest(slicer_cmd.suite())
   suite.addTest(slicer.suite())
   suite.addTest(viewer_cmd.suite())
   suite.addTest(determinator_cmd.suite())
   unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   main()


