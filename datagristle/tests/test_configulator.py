#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013,2017 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import os
import pytest
from pprint import pprint as pp

import datagristle.configulator as mod

GRISTLE_APP_NAME = 'gristle_fooper'
PGM_NAME = '/tmp/gristle_fooper.py'
SHORT_HELP = 'gristle_fooper short-help'
LONG_HELP = 'gristle_fooper long-help'



class TestEnvironmentalArgs(object):

    def setup_method(self, method):

        # setup app_config:
        config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        config.add_custom_config(name='delimiter',
                                 config_type=str,
                                 arg_type='option',
                                 default=None,
                                 help_msg=SHORT_HELP)
        config.add_custom_config(name='counter',
                                 config_type=int,
                                 arg_type='option',
                                 default=None,
                                 help_msg=SHORT_HELP)
        self.app_config = config.app_config
        pp(self.app_config)

    def teardown_method(self, method):
        try:
            os.environ.pop(f'{GRISTLE_APP_NAME}_delimiter')
        except KeyError:
            pass
        try:
            os.environ.pop(f'{GRISTLE_APP_NAME}_counter')
        except KeyError:
            pass


    def test_empty_environment(self):

        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self.app_config)
        env_config = env_args._get_gristle_app_args()
        assert env_config == {}


    def test_simple_environment_variable(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_delimiter'] = '$'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self.app_config)
        env_config = env_args._get_gristle_app_args()
        pp(env_config)
        assert env_config['delimiter'] == '$'


    def test_type_converted_environment_variable(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_counter'] = '999'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self.app_config)
        env_config = env_args._get_gristle_app_args()
        pp(env_config)
        assert env_config['counter'] == 999



class TestCommandLineArgs(object):

    def setup_method(self, method):

        # setup app_config:
        config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        config.add_custom_config(name='delimiter',
                                 config_type=str,
                                 arg_type='option',
                                 default=None,
                                 help_msg=SHORT_HELP)
        config.add_custom_config(name='counter',
                                 config_type=int,
                                 arg_type='option',
                                 default=None,
                                 help_msg=SHORT_HELP)

        self.app_config = config.app_config
        pp(self.app_config)

    def teardown_method(self, method):
        pass


    def test_empty_arguments(self):

        cli_args = mod._CommandLineArgs(SHORT_HELP, LONG_HELP, self.app_config)
        cli_config = cli_args.get_args([])
        assert cli_config == {'delimiter': None,
                              'counter': None,
                              'version': False,
                              'long_help': False}

    def test_simple_cli_argument(self):

        cli_args = mod._CommandLineArgs(SHORT_HELP, LONG_HELP, self.app_config)
        cli_config = cli_args.get_args(test_args=['--delimiter', '$'])
        assert cli_config == {'delimiter': '$',
                              'counter': None,
                              'version': False,
                              'long_help': False}

    def test_integer_cli_argument(self):

        cli_args = mod._CommandLineArgs(SHORT_HELP, LONG_HELP, self.app_config)
        cli_config = cli_args.get_args(test_args=['--counter', '999'])
        assert cli_config == {'delimiter': None,
                              'counter': 999,
                              'version': False,
                              'long_help': False}



class TestConfig(object):

    def setup_method(self, method):

        # setup app_config:
        self.config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        self.config.add_custom_config(name='delimiter',
                                      config_type=str,
                                      arg_type='option',
                                      default=None,
                                      help_msg=SHORT_HELP)
        self.config.add_custom_config(name='counter',
                                      config_type=int,
                                      arg_type='option',
                                      default=None,
                                      help_msg=SHORT_HELP)

        self.app_config = self.config.app_config
        pp(self.app_config)

    def teardown_method(self, method):
        try:
            os.environ.pop(f'{GRISTLE_APP_NAME}_delimiter')
        except KeyError:
            pass
        try:
            os.environ.pop(f'{GRISTLE_APP_NAME}_counter')
        except KeyError:
            pass


    def test_empty_args(self):
        config, nconfig = self.config.process_configs(test_cli_args=[])
        pp(nconfig)
        assert config['delimiter'] is None
        assert config['counter'] is None
        assert config['long_help'] is False
        assert config['version'] is False

        assert nconfig.delimiter == config['delimiter']
        assert nconfig.counter   == config['counter']
        assert nconfig.long_help == config['long_help']
        assert nconfig.version   == config['version']


    def test_cli_and_env_args(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_counter'] = '999'

        config, nconfig = self.config.process_configs(test_cli_args=['--delimiter', '$'])
        pp(nconfig)
        assert config['delimiter'] == '$'
        assert config['counter']   == 999
        assert config['long_help'] is False
        assert config['version'] is False


    def test_config_and_nconfig_consistency(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_counter'] = '999'

        config, nconfig = self.config.process_configs(test_cli_args=['--delimiter', '$'])
        pp(nconfig)
        assert config['delimiter'] == '$'
        assert config['counter']   == 999
        assert config['long_help'] is False
        assert config['version'] is False

        assert nconfig.delimiter == config['delimiter']
        assert nconfig.counter   == config['counter']
        assert nconfig.long_help == config['long_help']
        assert nconfig.version   == config['version']


    def test_cli_override_of_env(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_counter'] = '999'

        config, nconfig = self.config.process_configs(test_cli_args=['--counter', '777'])
        pp(nconfig)
        assert config['delimiter'] is None
        assert config['counter']   == 777
        assert config['long_help'] is False
        assert config['version'] is False


