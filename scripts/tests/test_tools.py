#!/usr/bin/env python
""" Provides tools to assist in testing.
"""
import imp
import os


def load_script(script_name):
    """ loads a script in the parent directory as a module, and passes back
        the module reference.  This is used when there is no .py suffix.

        Inputs:  the name of the script, without a directory
        Outputs: the module reference
    """

    test_dir              = os.path.dirname(os.path.realpath(__file__))
    script_dir            = os.path.dirname(test_dir)
    py_source_open_mode   = "U"
    py_source_description = (".py", py_source_open_mode, imp.PY_SOURCE)
    script_filepath       = os.path.join(script_dir, script_name)
    with open(script_filepath, py_source_open_mode) as script_file:
        mod = imp.load_module(script_name, script_file, script_filepath,  py_source_description)

    return mod


