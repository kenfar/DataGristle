#!/usr/bin/env python
""" The purpose of this module is to provide support for configuration data.

Configuration data can be provided three ways:
1. Command line arguments
2. Environmental variables
3. Defaults

This module was built in order to help reduce verbose & repetitive code within the CLI programs, which it
does by keeping STANDARD_CONFIGs full of common config items related to input & output filenames and CSV 
dialect options.

"""
import argparse
import collections
import copy
import os
from pprint import pprint as pp
import sys
from typing import List, Dict, Tuple, Any, Union, Callable, NamedTuple

from datagristle._version import __version__


CONFIG_TYPE = Dict[str, Any]
APP_CONFIG_TYPE = Dict[str, Dict[str, Any]]

STANDARD_CONFIGS: APP_CONFIG_TYPE = {}
STANDARD_CONFIGS['infiles'] = {'short_name': 'i',
                               'default': '-',
                               'required': True,
                               'help': "input filenames or default to for stdin",
                               'type': str,
                               'nargs': '*',
                               'arg_type': 'option'}
STANDARD_CONFIGS['outfile'] = {'short_name': 'o',
                               'default': '-',
                               'required': True,
                               'help': "output filename or '-' for stdout (the default)",
                               'type': str,
                               'arg_type': 'option'}
STANDARD_CONFIGS['delimiter'] = {'short_name': 'd',
                                 'default': None,
                                 'required': True,
                                 'help': 'csv delimiter',
                                 'type': str,
                                 'arg_type': 'option',
                                 'min_length': 1,
                                 'max_length': 1}
STANDARD_CONFIGS['quoting'] = {'short_name': 'q',
                               #'default': 'quote_none',
                               'default': None,
                               'required': True,
                               'choices': ['quote_all', 'quote_minimal',
                                           'quote_nonnumeric', 'quote_none'],
                               'help': 'csv quoting',
                               'type': str,
                               'arg_type': 'option'}
STANDARD_CONFIGS['quotechar'] = {'default': '"',
                                 'required': True,
                                 'help': 'csv quotechar',
                                 'type': str,
                                 'arg_type': 'option',
                                 'min_length': 1,
                                 'max_length': 1}
STANDARD_CONFIGS['escapechar'] = {'default': None,
                                  'required': True,
                                  'help': 'csv escapechar',
                                  'type': str,
                                  'arg_type': 'option',
                                  'min_length': 1,
                                  'max_length': 1}
STANDARD_CONFIGS['doublequote'] = {'default': None,
                                   'required': True,
                                   'help': 'csv dialect - quotes are escaped thru doublequoting',
                                   'type': bool,
                                   'arg_type': 'option',
                                   'action': 'store_const',
                                   'const': True}
STANDARD_CONFIGS['nodoublequote'] = {'default': None,
                                     'required': True,
                                     'help': 'csv dialect - quotes are escaped thru doublequoting',
                                     'type': bool,
                                     'arg_type': 'option',
                                     'action': 'store_const',
                                     'const': False}
STANDARD_CONFIGS['has_header'] = {'default': None,
                                  'required': True,
                                  'help': 'csv dialect - indicates header exists',
                                  'type': bool,
                                  'arg_type': 'option',
                                  'action': 'store_const',
                                  'const': True}
STANDARD_CONFIGS['has_no_header'] = {'default': None,
                                     'required': True,
                                     'help': 'csv dialect - indicates header exists',
                                     'type': bool,
                                     'arg_type': 'option',
                                     'action': 'store_const',
                                     'const': False,
                                     'dest': 'has_header'}
ARG_ONLY_CONFIGS = ['version', 'long_help']

VALID_ARG_TYPES = ('argument', 'option')



class Config(object):
    """ Manage the configuration items for your program.

    This class will gather config items from environmental variables and cli arguments,
    Then consolidate them,
    Then validate them,
    Then provide them back to your program as both a dictionary and NamedTuple

    Todo: add more validations:
      - add pattern - regex validation
      - add maximum & minimum - numeric ranges
      - add blank
      - add case?
    """

    def __init__(self, name: str, short_help: str, long_help: str) -> None:
        self.name = os.path.splitext(name)[0]
        self.short_help = short_help
        self.long_help = long_help
        self.app_config: APP_CONFIG_TYPE = {}
        self.config = None                      # final config dictionary
        self.named_config = None                # final config dictionary as namedtuple
        self.parser = None                      # argparser object - referenced here for error msging


    def add_standard_config(self, name):
        """ Add a standard config element for your app.
        These typically include entries for input & output files and csv dialects that most programs
        need - so they're considered "standard", are already defined and ready to be added to whichever
        programs need them.
        """
        self.app_config[name] = STANDARD_CONFIGS[name]


    def add_custom_config(self,
                          name: str,
                          default: Any,
                          config_type: Callable,
                          help_msg: str,
                          arg_type: str,
                          short_name: str = None,
                          nargs: str = None,
                          choices: List[str] = [],
                          dest: str = None):
        """ Add a custom config element (ex: --silent) for your app.
        This function will validate your configuration metadata,
        then will assign this metadata to the app config metadata - which will
        already have standard configuratio metadata for items like --delimiter.
        """

        # validation:
        assert arg_type in VALID_ARG_TYPES
        if short_name:
            assert len(short_name) == 1
        if dest:
            assert arg_type == 'bool'

        # assignment:
        self.app_config[name] = {'short_name': short_name,
                                 'default': default,
                                 'type': config_type,
                                 'help': help_msg,
                                 'arg_type': arg_type,
                                 'nargs': nargs,
                                 'choices': choices}

        if dest:
            self.app_config[name]['dest'] = dest

        # remove empty options:
        if self.app_config[name]['short_name'] is None:
            del self.app_config[name]['short_name']
        if self.app_config[name]['choices'] == []:
            del self.app_config[name]['choices']
        if self.app_config[name]['nargs'] is None:
            del self.app_config[name]['nargs']



    def apply_custom_defaults(self,
                              config: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Override this method to implement custom defaulting for your app
        """
        return config


    # Should this simply pass rather than raise an exception if not overridden?
    def validate_custom_config(self, config: CONFIG_TYPE) -> None:
        """Deprecated name - use custom_config_validator instead
        """
        raise NotImplementedError('should be overridden')

    def custom_config_validator(self, config: CONFIG_TYPE) -> None:
        """ Override this method to implement custom configurations for your app
        """
        self.validate_custom_config(config)



    def process_configs(self) -> Tuple[CONFIG_TYPE, collections.namedtuple]:
        """ Handles all config acqusition, consolidation, and validation.
        """
        self._validate_metadata()

        cli_args_manager = _CommandLineArgs(self.short_help, self.long_help, self.app_config)
        cli_args = cli_args_manager.args
        self.parser = cli_args_manager.parser
        #print('\n--------- arg -------------')
        #pp(cli_args)

        env_args_manager = _EnvironmentalArgs(self.name, self.app_config)
        env_args = env_args_manager.env_gristle_app_args
        #print('\n--------- env -------------')
        #pp(env_args)

        consolidated_config = self._consolidate_args(env_args, cli_args)
        #pp('\n--------- consolidated -------------\n')
        #pp(consolidated_config)

        defaulted_config = self._apply_std_defaults(consolidated_config)
        final_config = self.apply_custom_defaults(defaulted_config)
        #print('\n--------- final -------------')
        #pp(final_config)

        self._config_validator(final_config)
        self.custom_config_validator(final_config)
        #print('\n--------- validation complete-------------')

        self.named_config = collections.namedtuple('Config', final_config.keys())(**final_config)
        self.config = final_config

        return self.config, self.named_config



    def _validate_metadata(self):
        """ Validates config metadata in self.app_config

        Does not validate the user-provided values - just the metadata in our code to confirm
        that we haven't screwed up the parameters.

        Additional checks we could make:
             assert that we don't have combo: positional long name + short_name
             assert that we don't have > 1 positional arguments
             assert that we don't have combo: choices + type boolean
        """
        for arg, arg_parameters in self.app_config.items():
            for property_name, property_value in arg_parameters.items():
                if property_name == 'short_name':
                    if len(property_value) != 1:
                        raise ValueError(f'{arg}.short_name length is invalid')
                elif property_name == 'default':
                    if property_value is not None:
                        if type(property_value) is not self.app_config[arg]['type']:
                            raise ValueError(f'{arg}.default type is invalid: {property_value}')
                elif property_name == 'required':
                    if type(property_value) is not type(True):
                        raise ValueError(f'{arg}.required type is invalid: {property_value}')
                elif property_name == 'help':
                    if not isinstance(property_value, str):
                        raise ValueError(f'{arg}.help type is invalid: {property_value}')
                elif property_name == 'type':
                    if not isinstance(property_value, type):
                        raise ValueError(f"{arg}.type's type is invalid: {property_value}")
                elif property_name == 'arg_type':
                    if property_value not in ('option', 'argument'):
                        raise ValueError(f"{arg}.arg_type's value is invalid: {property_value}")
                elif property_name == 'nargs':
                    if property_value not in ('*', '?', '+'):
                        raise ValueError(f"{arg}.narg's value is invalid: {property_value}")
                elif property_name == 'choices':
                    if not isinstance(property_value, list):
                        raise ValueError(f"{arg}.choice type is not a list")
                elif property_name == 'min_length':
                    if not int(property_value):
                        raise ValueError(f"{arg}.min_length is not an int")
                elif property_name == 'max_length':
                    if not int(property_value):
                        raise ValueError(f"{arg}.max_length is not an int")
                elif property_name == 'action':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"dest is only valid for type of bool")
                    if property_value not in ('store_const'):
                        raise ValueError(f"{arg}.action is not 'store_const'")
                elif property_name == 'dest':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"dest is only valid for type of bool")
                elif property_name == 'const':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"const is only valid for type of bool")
                else:
                    raise ValueError(f'unknown app_config property: {arg}.{property_name}')



    def _consolidate_args(self,
                          env_args: CONFIG_TYPE,
                          cli_args: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Consolidates environmental and cli arguments.

        First all app_config keys are added,
        Then values from matching environmental variable keys are overlaid,
        Finally values from matching cli arg keys are overlaid,
        """
        consolidated_args = {}

        for key in self.app_config:
            actual_key = self.app_config[key].get('dest', key)
            consolidated_args[actual_key] = None

        for key, val in env_args.items():
            actual_key = self.app_config[key].get('dest', key)
            consolidated_args[actual_key] = val

        for key, val in cli_args.items():
            if val is not None:
                consolidated_args[key] = val

        return consolidated_args


    def _apply_std_defaults(self,
                            config: CONFIG_TYPE) -> CONFIG_TYPE:
        temp_config = copy.copy(config)
        for key, val in temp_config.items():
            if val is None:
                temp_config[key] = self.app_config[key].get('default')
        return temp_config


    def _config_validator(self,
                          config: CONFIG_TYPE) -> None:
        """ validates the consolidated config

        This function applies standard validations, which currently include:
            - type-checking
            - min_length
            - max_length
        In the future we should probably also add:
            - combination checking:
                -- escapechar & doublequote are not valid together
                -- quote_none & quotechar are not valid together
            - add nargs to type-checking
        """

        for key, val in config.items():
            if key in ARG_ONLY_CONFIGS:
                continue
            if 'nargs' in self.app_config[key]:
                continue
            if val is not None:
                if not isinstance(val, self.app_config[key]['type']):
                    raise TypeError('key: "{}" with value: "{}" is not type: {}'
                                    .format(key, val, self.app_config[key]['type']))
                if 'min_length' in self.app_config[key]:
                    if len(val) < self.app_config[key]['min_length']:
                        raise ValueError('key "{}" with value "{}" is shorter than min_length of {}'
                                         .format(key, val, self.app_config[key]['min_length']))
                if 'max_length' in self.app_config[key]:
                    if len(val) > self.app_config[key]['max_length']:
                        raise ValueError('key "{}" with value "{}" is longer than max_length of {}'
                                         .format(key, val, self.app_config[key]['max_length']))





class _EnvironmentalArgs(object):
    """ Manages all environmental configuration arguments related to the gristle app

        This class will collect these arguments from the environment,
        format them,
        then provide them via class attributes:
           self.env_gristle_app_args
    """

    def __init__(self,
                 gristle_app_name: str,
                 app_config: APP_CONFIG_TYPE) -> None:

        self.gristle_app_name = gristle_app_name
        self.app_config = app_config
        self.env_args = os.environ.items()
        self.env_gristle_app_args = self._get_gristle_app_args()

    def _get_gristle_app_args(self) -> CONFIG_TYPE:
        """ Returns a dictionary of environment keys & vals associated with the calling program.

        Note that the vals will be converted to the appropriate type.
        """
        env_config = {}
        for envkey, envval in self.env_args:
            if envkey in self._transform_config_keys_to_env_keys():
                option_name = self._transform_env_key_to_option_name(envkey)
                if self.app_config[option_name]['type'] is bool:
                    if self.app_config[option_name].get('dest', option_name) == option_name:
                        # issue: assumes env true/false matches app_config 'store_true'/'store_false'
                        env_config[option_name] = self.app_config[option_name]['type'](envval)
                    else:
                        pass # ignore booleans used to reverse a different boolean
                else:
                    env_config[option_name] = self.app_config[option_name]['type'](envval)
        return env_config

    def _transform_config_keys_to_env_keys(self):
        """ Translates the configuration keys to the env key formats by adding
            'gristle_[app_name] as a prefix to each key.
        """
        env_keys = [f'{self.gristle_app_name}_{key}' for key in self.app_config.keys()]
        return env_keys

    def _transform_env_key_to_option_name(self,
                                          envkey: str) -> str:
        """ Translates environment key to our option name format by stripping
            'gristle_[app_name]_' from the front of the env key
        """
        option_name = envkey[len(f'{self.gristle_app_name}_'):]
        return option_name



class _CommandLineArgs(object):
    """ Manages commandline arguments.

    This class will:
        - generate the ArgParse configuration,
        - parse the arguments
        - respond to certain arguments (--long-help & --version)
        - then provide results in dictinary form via internal attribute:
            - self.args
    """

    def __init__(self,
                 short_help: str,
                 long_help: str,
                 app_config_metadata: APP_CONFIG_TYPE) -> None:

        self.short_help = short_help
        self.long_help = long_help
        self.app_config_metadata = app_config_metadata
        self.args = self._get_args()                    # Will be referenced by calling code
        self.parser = None                              # Will be referenced by calling code


    def _get_args(self) -> CONFIG_TYPE:
        """ Build an argparser, parse the arguments, and return the results as a dict
        """
        self._make_argparse_parser_from_app_config_metadata()

        allargs = self.parser.parse_args()
        if allargs.version:
            print(__version__)
            sys.exit(0)
        if allargs.long_help:
            print(self.long_help)
            sys.exit(0)

        return vars(allargs)


    def _make_argparse_parser_from_app_config_metadata(self):
        """ Build the entire argparser - for all arguments from app_config_metadtaa
        """

        self.parser = argparse.ArgumentParser(self.short_help)

        for key in self.app_config_metadata:
            self._make_one_argparser_argument_from_app_config_metadata(key)

        # fixme: these should just be standard configs, they're added here so that each program
        # doesn't have to add them.
        self.parser.add_argument('-V', '--version',
                                 action='store_true',
                                 default=False,
                                 help='show version number then exit')
        self.parser.add_argument('--long-help',
                                 action='store_true',
                                 default=False,
                                 help='Print more verbose help')


    def _make_one_argparser_argument_from_app_config_metadata(self,
                                                              key: str):
        """ Add a single argument to parser based on app_config key
        """

        #fixme: can only handle 1 positional argument: it doesn't actually have 'position' for positionals
        #self.parser = argparse.ArgumentParser(desc, argument_default=argparse.SUPPRESS)

        args = []               # values are formatted options like ['-i', '--infile']
        arg_properties = {}     # keys are properties like 'type', 'default'
        arg_metadata = self.app_config_metadata[key]

        #---------- Add args: ----------------

        long_name = (f'--{key}' if arg_metadata['arg_type'] == 'option' else key).replace('_', '-')
        short_name_unformatted = arg_metadata.get('short_name', '')
        short_name = f"-{short_name_unformatted}" if short_name_unformatted else ''

        if short_name:
            args.append(short_name)
        args.append(long_name)

        #---------- Add arg_properties: ----------------

        def arg_properties_simple_assigner(key):
            if key in arg_metadata:
                arg_properties[key] = arg_metadata[key]

        arg_properties_simple_assigner('nargs')
        arg_properties_simple_assigner('help')
        arg_properties_simple_assigner('choices')

        if arg_metadata['arg_type'] == 'argument':
            arg_properties['default'] = arg_metadata['default']
        elif arg_metadata['type'] is bool:
            if 'action' in arg_metadata:
                arg_properties['action'] = arg_metadata['action']
                arg_properties['const'] = arg_metadata['const']
            if 'dest' in arg_metadata:
                arg_properties['dest'] = arg_metadata['dest']
        else:
            arg_properties['type'] = arg_metadata['type'] # don't include type for booleans

        self.parser.add_argument(*args, **arg_properties)






