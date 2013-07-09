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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.common  as mod


class TestFunctions():

    def test_get_common_key(self):
        d = {'car': 7, 'truck':8, 'boat':30, 'plane': 5}
        assert mod.get_common_key(d) == ('boat',0.6)
