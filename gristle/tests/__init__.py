#!/usr/bin/env python

import os
import sys
import unittest
import test_field_determinator
import test_field_math
import test_field_misc
import test_field_type
import test_file_type
import test_metadata
import test_simplesql

def main():

   suite  = unittest.TestSuite()
   suite.addTest(test_field_determinator.suite())
   suite.addTest(test_field_math.suite())
   suite.addTest(test_field_misc.suite())
   suite.addTest(test_field_type.suite())
   suite.addTest(test_file_type.suite())
   suite.addTest(test_metadata.suite())
   suite.addTest(test_simplesql.suite())
   unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
   #print os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
   main()

