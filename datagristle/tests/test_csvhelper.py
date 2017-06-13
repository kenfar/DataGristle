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
import pytest
import csv
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))
sys.path.insert(0, dirname(dirname(os.path.abspath(__file__))))
import datagristle.csvhelper as mod


class TestDialect(object):

    def test_basics(self):
        foo = mod.Dialect
        print(type(foo))
        print(type(csv.Dialect))
        assert type(foo) ==  type(csv.Dialect)

