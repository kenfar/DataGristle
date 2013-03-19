#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""
import sys
import os
import tempfile
import random
import atexit
import shutil
try:
    import unittest2 as unittest
except ImportError:
    import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.common  as mod


class TestFunctions(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_get_common_key(self):
        d = {'car': 7, 'truck':8, 'boat':30, 'plane': 5}
        self.assertEqual(mod.get_common_key(d), ('boat',0.6))
