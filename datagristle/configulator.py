#!/usr/bin/env python

""" Manages user config - arguments and environmental variables.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2020 Ken Farmer
"""

import sys
import argparse
import collections
import copy
import os
from pprint import pprint as pp
from typing import List, Dict, Tuple, Any, Union, Callable, Optional, NamedTuple

from datagristle._version import __version__
import datagristle.csvhelper as csvhelper


CONFIG_TYPE = Dict[str, Any]
META_CONFIG_TYPE = Dict[str, Dict[str, Any]]
STANDARD_CONFIGS: META_CONFIG_TYPE = {}
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
                                  'arg_type': 'option'}
STANDARD_CONFIGS['doublequote'] = {'default': None,
                                   'required': True,
                                   'help': 'csv dialect - quotes are escaped thru doublequoting',
                                   'type': bool,
                                   'arg_type': 'option',
                                   'action': 'store_const',
                                   'const': True}
STANDARD_CONFIGS['no_doublequote'] = {'default': None,
                                      'required': True,
                                      'help': 'csv dialect - quotes are escaped thru doublequoting',
                                      'type': bool,
                                      'arg_type': 'option',
                                      'action': 'store_const',
                                      'const': False,
                                      'dest': 'doublequote'}
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

    # next - add more validations:
    #  - add pattern - regex validation
    #  - add maximum & minimum - numeric ranges
    #  - add blank
    #  - add case?

    def __init__(self, name: str, short_help: str, long_help: str) -> None:
        self.name = os.path.splitext(name)[0]
        self.short_help = short_help
        self.long_help = long_help
        self.meta_config: META_CONFIG_TYPE = {}
        self.config: Dict = {}
        self.nconfig: Optional[NamedTuple] = None

    def add_custom_config(self,
                          name: str,
                          config_type: Callable,
                          help_msg: str,
                          arg_type: str,
                          default: Any = None,
                          required: bool = False,
                          action: Optional[str] = None,
                          const: Any = None,
                          short_name: Optional[str] = None,
                          nargs: Optional[str] = None,
                          choices: List[str] = [],
                          dest: Optional[str] = None):
        assert arg_type in VALID_ARG_TYPES
        self.meta_config[name] = {'default': default,
                                  'type': config_type,
                                  'help': help_msg,
                                  'arg_type': arg_type,
                                  'required': required}
        if short_name:
            self.meta_config[name]['short_name'] = short_name
        if choices:
            self.meta_config[name]['choices'] = choices
        if nargs:
            self.meta_config[name]['nargs'] = nargs
        if action:
            self.meta_config[name]['action'] = action
            self.meta_config[name]['const'] = const
        if arg_type is bool:
            self.meta_config[name]['dest'] = dest or name


    def add_standard_config(self, name):
        self.meta_config[name] = STANDARD_CONFIGS[name]


    def add_all_csv_configs(self):
        """ Adds the whole standard set of csv config items.

        This is how all csv utilities should pick these up - rather than doing it individually.
        """
        self.add_standard_config('delimiter')
        self.add_standard_config('quoting')
        self.add_standard_config('quotechar')
        self.add_standard_config('doublequote')
        self.add_standard_config('no_doublequote')
        self.add_standard_config('escapechar')
        self.add_standard_config('has_header')
        self.add_standard_config('has_no_header')


    def process_configs(self):
        self._validate_metadata()

        arg_config = self._get_arg_config(self.short_help)
        env_config = self._get_env_config()
        consolidated_config = self._consolidate_configs(env_config, arg_config)

        defaulted_config = self._apply_std_defaults(consolidated_config)
        final_config = self.apply_custom_defaults(defaulted_config)

        self._validate_std_config(final_config)
        self.validate_custom_config(final_config)

        self.replace_configs(final_config)


    def replace_configs(self, new_config):
        """ Replaces the dictionary and named-tuple versions of the config
        """
        self.config = new_config
        self.nconfig = collections.namedtuple('Config', self.config.keys())(**self.config)


    def update_config(self, key, value):
        """ Writes a key-value to the config.
        """
        self.config[key] = value
        self.nconfig = collections.namedtuple('Config', self.config.keys())(**self.config)


    def generate_csv_dialect_config(self):
        """ Replaces the dictionary and named-tuple versions of the config
        """
        self.update_config('dialect', csvhelper.get_dialect(self.nconfig.infiles,
                                                            self.nconfig.delimiter,
                                                            self.nconfig.quoting,
                                                            self.nconfig.quotechar,
                                                            self.nconfig.has_header,
                                                            self.nconfig.doublequote,
                                                            self.nconfig.escapechar))

    def _validate_metadata(self):
        """ Validates the program's configuration metadata (not the user's input).

        """
        # additional checks we could make:
        #     assert that we don't have combo: positional long name + short_name
        #     assert that we don't have > 1 positional arguments
        #     assert that we don't have combo: choices + type boolean
        for arg, arg_parameters in self.meta_config.items():
            for property_name, property_value in arg_parameters.items():
                if property_name == 'short_name':
                    if len(property_value) != 1:
                        raise ValueError(f'{arg}.short_name length is invalid')
                elif property_name == 'default':
                    if property_value is not None:
                        if type(property_value) is not self.meta_config[arg]['type']:
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
                    if property_value not in ('store_const', 'store_true'):
                        raise ValueError(f"{arg}.action is not 'store_const'")
                elif property_name == 'dest':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"dest is only valid for type of bool")
                elif property_name == 'const':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"const is only valid for type of bool")
                else:
                    raise ValueError(f'unknown meta_config property: {arg}.{property_name}')


    def _get_arg_config(self, desc: str) -> CONFIG_TYPE:
        """ Gets config items from cli arguments.
        """
        #fixme: can only handle 1 positional argument: it doesn't actually have 'position' for positionals
        self.parser = argparse.ArgumentParser(desc)
        for key in self.meta_config:
            long_name = (f'--{key}' if self.meta_config[key]['arg_type'] == 'option' else key).replace('_', '-')
            skey = self.meta_config[key].get('short_name', '').replace('_', '-')
            short_name = f'-{skey}'

            args = []
            kwargs = {}

            if skey:
                args.append(short_name)
            args.append(long_name)
            if self.meta_config[key]['arg_type'] == 'argument':
                kwargs['default'] = self.meta_config[key]['default']
            if 'nargs' in self.meta_config[key]:
                kwargs['nargs'] = self.meta_config[key]['nargs']

            kwargs['help'] = self.meta_config[key]['help']
            if 'choices' in self.meta_config[key]:
                kwargs['choices'] = self.meta_config[key]['choices']
            if self.meta_config[key]['type'] is bool:
                if 'action' in self.meta_config[key]:
                    kwargs['action'] = self.meta_config[key]['action']
                    if self.meta_config[key].get('const') is not None:
                        kwargs['const'] = self.meta_config[key]['const']
                    if self.meta_config[key]['action'] == 'store_true':
                        kwargs['const'] = True
                if 'dest' in self.meta_config[key]:
                    kwargs['dest'] = self.meta_config[key]['dest']
            else:
                kwargs['type'] = self.meta_config[key]['type'] # don't include type for booleans

            pp(kwargs)
            self.parser.add_argument(*args, **kwargs)

        self.parser.add_argument('-V', '--version',
                                 action='store_true',
                                 default=False,
                                 help='show version number then exit')

        self.parser.add_argument('--long-help',
                                 action='store_true',
                                 default=False,
                                 help='Print more verbose help')

        allargs = self.parser.parse_args()
        if allargs.version:
            print(__version__)
            sys.exit(0)
        if allargs.long_help:
            print(self.long_help)
            sys.exit(0)

        return vars(allargs)



    def _get_env_config(self) -> CONFIG_TYPE:
        """ Gets config items from environmental variables.
        """
        env_config= {}
        for envkey, envval in os.environ.items():
            if envkey in ['%s_' % self.name + x for x in self.meta_config.keys()]:
                short_key = envkey[len('%s_' % self.name):]
                if self.meta_config[short_key]['type'] is bool:
                    if self.meta_config[short_key]['dest'] == short_key:
                        # issue: assumes env true/false matches meta_config 'store_true'/'store_false'
                        env_config[short_key] = self.meta_config[short_key]['type'](envval)
                    else:
                        pass # ignore booleans used to reverse a different boolean
                else:
                    env_config[short_key] = self.meta_config[short_key]['type'](envval)
        return env_config


    def _consolidate_configs(self, envvars: CONFIG_TYPE, args: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Consolidates environmental and cli configs.
        """
        consolidated_config = {}
        for key in self.meta_config:
            if 'dest' in self.meta_config[key]:
                consolidated_config[self.meta_config[key]['dest']] = None
            else:
                consolidated_config[key] = None
        for key, val in envvars.items():
            if self.meta_config[key]['dest']:
                consolidated_config[self.meta_config[key]['dest']] = val
            else:
                consolidated_config[key] = val
        for key, val in args.items():
            if val is not None:
                consolidated_config[key] = val
        return consolidated_config


    def _apply_std_defaults(self, config: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Applies defaults to standard config items.
        """
        temp_config = copy.copy(config)
        for key, val in temp_config.items():
            if val is None:
                temp_config[key] = self.meta_config[key].get('default')
        return temp_config


    def apply_custom_defaults(self, config: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Applies defaults to custom config items.

        This is intended to be overriden by the user.
        """
        return config


    def _validate_std_config(self, config: CONFIG_TYPE) -> None:
        """ Validates standard config items.
        """
        for key, val in config.items():
            if key in ARG_ONLY_CONFIGS:
                continue
            if 'nargs' in self.meta_config[key]:
                continue
            if val is not None:
                if not isinstance(val, self.meta_config[key]['type']):
                    raise TypeError('key: "{}" with value: "{}" is not type: {}'
                                    .format(key, val, self.meta_config[key]['type']))
                if 'min_length' in self.meta_config[key]:
                    if len(val) < self.meta_config[key]['min_length']:
                        raise ValueError('key "{}" with value "{}" is shorter than min_length of {}'
                                         .format(key, val, self.meta_config[key]['min_length']))
                if 'max_length' in self.meta_config[key]:
                    if len(val) > self.meta_config[key]['max_length']:
                        raise ValueError('key "{}" with value "{}" is longer than max_length of {}'
                                         .format(key, val, self.meta_config[key]['max_length']))



    def validate_custom_config(self, config: CONFIG_TYPE) -> None:
        """ Validates custom config items.

        This is intended to be overriden by the user.
        """
        raise NotImplementedError('should be overridden')


