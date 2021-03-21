#!/usr/bin/env python

""" Manages user config - arguments and environmental variables.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2020-2021 Ken Farmer

    Challenges:
    1. config files are hierarchical, args & envs are flat
    2. cli args and config keys have dashes, envvars have underscores
    3. some input is intended to be interactive-only - such as --version, --help, --long-help
"""

import argparse
import collections
import copy
import json
import os
from os.path import isfile, splitext, basename, isabs, dirname, abspath, join as pjoin, exists
from pprint import pprint as pp
import sys
from typing import List, Dict, Any, Callable, Optional, NamedTuple

import ruamel.yaml as yaml

from datagristle._version import __version__
import datagristle.common as comm
import datagristle.csvhelper as csvhelper


CONFIG_TYPE = Dict[str, Any]
META_CONFIG_TYPE = Dict[str, Dict[str, Any]]
METADATA_TYPE = Dict[str, Dict[str, Any]]


def transform_delimiter(val):
    if val is None:
        return val
    else:
        return comm.dialect_del_fixer(val)

def transform_lower(val):
    if val is None:
        return None
    else:
        return val.lower()


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
                                 'help': 'csv delimiter',
                                 'type': str,
                                 'arg_type': 'option',
                                 'min_length': 1,
                                 'max_length': 1,
                                 'transformer': transform_delimiter}
STANDARD_CONFIGS['quoting'] = {'short_name': 'q',
                               'default': None,
                               'choices': ['quote_all', 'quote_minimal',
                                           'quote_nonnumeric', 'quote_none'],
                               'help': 'csv quoting',
                               'type': str,
                               'arg_type': 'option',
                               'transformer': transform_lower}
STANDARD_CONFIGS['quotechar'] = {'default': '"',
                                 'help': 'csv quotechar',
                                 'type': str,
                                 'arg_type': 'option',
                                 'min_length': 1,
                                 'max_length': 1}
STANDARD_CONFIGS['escapechar'] = {'default': None,
                                  'help': 'csv escapechar',
                                  'type': str,
                                  'arg_type': 'option'}
STANDARD_CONFIGS['doublequote'] = {'default': False,
                                   'help': 'csv dialect - quotes are escaped thru doublequoting',
                                   'type': bool,
                                   'arg_type': 'option',
                                   'action': 'store_const',
                                   'const': True}
STANDARD_CONFIGS['no_doublequote'] = {'required': True,
                                      'help': 'csv dialect - quotes are not escaped thru doublequoting',
                                      'type': bool,
                                      'arg_type': 'option',
                                      'action': 'store_const',
                                      'const': False,
                                      'dest': 'doublequote'}
STANDARD_CONFIGS['has_header'] = {'default': None,
                                  'help': 'csv dialect - indicates header exists',
                                  'type': bool,
                                  'arg_type': 'option',
                                  'action': 'store_const',
                                  'const': True}
STANDARD_CONFIGS['has_no_header'] = {'default': None,
                                     'help': 'csv dialect - indicates no header exists',
                                     'type': bool,
                                     'arg_type': 'option',
                                     'action': 'store_const',
                                     'const': False,
                                     'dest': 'has_header'}

STANDARD_CONFIGS['verbosity'] = {'default': 'normal',
                                 'help': 'controls level of logging - with quiet, normal, high, debug levels',
                                 'type': str,
                                 'choices': ['quiet', 'normal', 'high', 'debug'],
                                 'arg_type': 'option'}

STANDARD_CONFIGS['dry_run'] = {'default': False,
                               'help': 'Performs most processing except for final changes or output',
                               'type': bool,
                               'arg_type': 'option',
                               'action': 'store_const',
                               'const': True}

STANDARD_CONFIGS['config_fn'] = {'default': None,
                                 'help': 'Name of config file',
                                 'type': str,
                                 'arg_type': 'option'}
STANDARD_CONFIGS['gen_config_fn'] = {'default': None,
                                     'help': 'Generates a config file',
                                     'type': str,
                                     'arg_type': 'option'}

STANDARD_CONFIGS['help'] = {'short_name': 'h',
                            'default': None,
                            'help': 'Displays short help info and exits',
                            'type': bool,
                            'action': 'store_const',
                            'const': True,
                            'arg_type': 'option'}




ARG_ONLY_CONFIGS = ['version', 'long_help', 'config_fn', 'long-help']
VALID_ARG_TYPES = ('argument', 'option')



class Config(object):

    def __init__(self,
                 app_name: str,
                 short_help: str,
                 long_help: str) -> None:

        self.app_name = splitext(basename(app_name))[0]
        self.short_help = short_help
        self.long_help = long_help
        self.obsolete_options = {}
        self._app_metadata: META_CONFIG_TYPE = {}
        self.config: Dict = {}
        self.nconfig: Optional[NamedTuple] = None


    def add_obsolete_metadata(self,
                              name,
                              short_name,
                              msg) -> None:
        self.obsolete_options[f'--{name}'] = msg
        self.obsolete_options[f'-{short_name}'] = msg


    def add_custom_metadata(self, name, **kwargs):
        for (key, val) in kwargs.items():
            if name not in self._app_metadata:
                self._app_metadata[name] = {}
            self._app_metadata[name][key] = val

        assert self._app_metadata[name]['arg_type'] in VALID_ARG_TYPES
        if self._app_metadata[name]['arg_type'] == 'bool':
            if 'dest' not in self._app_metadata[name]:
                self._app_metadata[name]['dest'] = name


    def add_standard_metadata(self, name):
        self._app_metadata[name] = STANDARD_CONFIGS[name]


    def add_all_csv_configs(self):
        """ Adds the whole standard set of csv config items.
        """
        self.add_standard_metadata('delimiter')
        self.add_standard_metadata('quoting')
        self.add_standard_metadata('quotechar')
        self.add_standard_metadata('escapechar')
        self.add_standard_metadata('doublequote')
        self.add_standard_metadata('no_doublequote')
        self.add_standard_metadata('has_header')
        self.add_standard_metadata('has_no_header')


    def add_all_config_configs(self):
        """ Adds the standard set of config items.
        """
        self.add_standard_metadata('config_fn')
        self.add_standard_metadata('gen_config_fn')


    def add_all_help_configs(self):
        """ Adds the standard set of help items.
        """
        self.add_standard_metadata('help')



    def process_configs(self,
                        test_cli_args: List = None):

        self._validate_metadata()

        # Get inputs from all three interfaces:
        env_args_manager = _EnvironmentalArgs(self.app_name, self._app_metadata)
        env_args = env_args_manager.env_gristle_app_args

        cli_args_manager = _CommandLineArgs(self.short_help, self.long_help, self._app_metadata, self.obsolete_options)
        cli_args_manager._get_args(test_cli_args)
        cli_args = cli_args_manager.cli_args

        config_fn = cli_args.get('config_fn', None) or env_args.get('config_fn', None)
        if config_fn:
            file_args_manager = _FileArgs(config_fn)
            file_config = file_args_manager.file_gristle_app_args
        else:
            file_config = {}

        # Consolidate inputs:
        consolidated_config = self._consolidate_configs(file_config, env_args, cli_args)

        # Apply Defaults:
        defaulted_config = self._apply_std_defaults(consolidated_config)
        defaulted_config = self.apply_custom_defaults(defaulted_config)

        # Apply Transforms:
        transformed_config = self.transform_config(defaulted_config)

        # Validate:
        self._validate_std_config(transformed_config)
        self.validate_custom_config(transformed_config)

        # Update and rebuild object configs:
        self.replace_configs(transformed_config)

        # Generate config file
        if self.config.get('gen_config_fn'):
            self.generate_config_file()


    def generate_config_file(self):
        with open(self.nconfig.gen_config_fn, 'w') as outbuf:
            if self.nconfig.gen_config_fn.endswith('.yml'):
                filtered_config = {k:v for k,v in self.config.items() if k not in ARG_ONLY_CONFIGS}
                filtered_config = {k:v for k,v in filtered_config.items() if k != 'gen_config_fn'}
                yaml.dump(filtered_config, outbuf, indent=4)
            elif self.nconfig.gen_config_fn.endswith('.json'):
                json.dump(self.config, outbuf)


    def transform_config(self, config):
        for key, val in config.items():

            if key in ARG_ONLY_CONFIGS:
                continue

            transformer = self._app_metadata[key].get('transformer')
            if transformer:
                try:
                    config[key] = transformer(val)
                except ValueError:
                    print(f'ERROR with input {key}')
                    raise

        # fix incorrect types coming in from config files
        for key, val in config.items():
            if key in ARG_ONLY_CONFIGS:
                continue
            intended_type = self._app_metadata[key]['type']
            if intended_type is str:
                if type(val) is int:
                    config[key] = str(val)

        return config


    def replace_configs(self, new_config):
        """ Replaces the dictionary and named-tuple versions of the config
        """
        self.config = new_config
        self.nconfig = collections.namedtuple('Config', self.config.keys())(**self.config)


    def update_config(self, key, value):
        """ Writes a key-value to the config.
        """
        new_config = {**self.config, **{key: value}}
        self.replace_configs(new_config)


    def generate_csv_dialect_config(self):
        """ Replaces the dictionary and named-tuple versions of the config
        """
        self.update_config('dialect', csvhelper.get_dialect(self.nconfig.infiles,
                                                            self.nconfig.delimiter,
                                                            self.nconfig.quoting,
                                                            self.nconfig.quotechar,
                                                            self.nconfig.has_header,
                                                            self.nconfig.doublequote,
                                                            self.nconfig.escapechar,
                                                            self.nconfig.verbosity))

    def _validate_metadata(self):
        """ Validates the program's configuration metadata (not the user's input).

        """
        # additional checks we could make:
        #     assert that we don't have combo: positional long name + short_name
        #     assert that we don't have > 1 positional arguments
        #     assert that we don't have combo: choices + type boolean
        for arg, arg_parameters in self._app_metadata.items():
            for property_name, property_value in arg_parameters.items():
                if property_name == 'short_name':
                    if len(property_value) != 1:
                        raise ValueError(f'{arg}.short_name length is invalid')
                elif property_name == 'default':
                    if property_value is not None:
                        if type(property_value) is not self._app_metadata[arg]['type']:
                            raise ValueError(f'{arg}.default type is invalid: {property_value}')
                elif property_name == 'required':
                    if type(property_value) is not type(True):
                        raise ValueError(f'{arg}.required type is invalid: {property_value}')
                elif property_name == 'help':
                    if not isinstance(property_value, str):
                        raise ValueError(f'{arg}.help type is invalid: {property_value}')
                elif property_name == 'type':
                    if type(property_value) == type([]):
                        for item in property_value:
                            if not isinstance(item, type):
                                raise ValueError(f"{arg}.type's type within the union is invalid: {property_value}")
                    elif not isinstance(property_value, type):
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
                elif property_name == 'minimum':
                    if not int(property_value):
                        raise ValueError(f"{arg}.minimum is not an int")
                elif property_name == 'maximum':
                    if not int(property_value):
                        raise ValueError(f"{arg}.maximum is not an int")

                elif property_name == 'action':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"{arg}.action is only valid for type of bool")
                    if property_value not in ('store_const', 'store_true'):
                        raise ValueError(f"{arg}.action is not 'store_const'")
                elif property_name == 'dest':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"{arg}.dest is only valid for type of bool")
                elif property_name == 'const':
                    if arg_parameters['type'] is not bool:
                        raise ValueError(f"{arg}.const is only valid for type of bool")
                elif property_name == 'transformer':
                    pass
                else:
                    raise ValueError(f'unknown meta_config property: {arg}.{property_name}')


    def _consolidate_configs(self,
                             file_args: CONFIG_TYPE,
                             env_args: CONFIG_TYPE,
                             cli_args: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Consolidates environmental and cli arguments.

        First all _app_metadata keys are added,
        Then values from matching environmental variable keys are overlaid,
        Finally values from matching cli arg keys are overlaid,
        """
        consolidated_args = {}

        for key in self._app_metadata:
            actual_key = self._app_metadata[key].get('dest', key)
            consolidated_args[actual_key] = None

        try:
            for key, val in file_args.items():
                actual_key = self._app_metadata[key].get('dest', key)
                consolidated_args[actual_key] = val
        except KeyError as e:
            comm.abort(f'ERROR: Unregistered arg: {key}')

        for key, val in env_args.items():
            actual_key = self._app_metadata[key].get('dest', key)
            consolidated_args[actual_key] = val

        for key, val in cli_args.items():
            if val is not None:
                consolidated_args[key] = val

        return consolidated_args


    def _apply_std_defaults(self, config: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Applies defaults to standard config items.
        """
        temp_config = copy.copy(config)
        for key, val in temp_config.items():
            if val is None:
                temp_config[key] = self._app_metadata[key].get('default')
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
            if key == 'col_names':
                # otherwise has issues with checks below.  Should make this exclusion more generic.
                continue
            if val is None or val == []:
                if self._app_metadata[key].get('required'):
                    comm.abort(f"Error:  option '{key}' was not provided but is required")
            else:
                if 'nargs' in self._app_metadata[key]:
                    continue
                else:

                    required = self._app_metadata[key]

                    if not isinstance(val, required['type']):
                        comm.abort('Error: config value has the wrong type',
                                   f"'{key}' with value: '{val}' is not {required['type']}")

                    if 'min_length' in required:
                        if len(val) < required['min_length']:
                            comm.abort('Error: config value is under min_length',
                                       f"'{key}' with len of value '{val}' is < {required['min_length']}")

                    if 'max_length' in required:
                        if len(val) > required['max_length']:
                            comm.abort("Error: config value is over max_length",
                                       f"'{key}' with len of value '{val}' is > {required['max_length']}")

                    if 'minimum' in required:
                        if val < required['minimum']:
                            comm.abort(f"Error: config value less than minimum",
                                       f"'{key}' with value of '{val}' is < {required['minimum']}")

                    if 'maximum' in required:
                        if val > required['maximum']:
                            comm.abort(f"Error: config value greater than maximum",
                                       f"'{key}' with value of '{val}' is > {required['maximum']}")

                    if 'choices' in required:
                        if val not in required['choices']:
                            comm.abort(f"Error: config value not in valid list of choices",
                                       f"Valid values include: {required['choices']} ")

        self._validate_dialect_with_stdin(config)


    def _validate_dialect_with_stdin(self, config) -> None:
        if (config['infiles'] == '-'
            and (config['delimiter'] is None
                 or config['quoting'] is None
                 or config['has_header'] is None)):
                comm.abort('Error: csv dialect is required when piping data via stdin')



    def validate_custom_config(self, config: CONFIG_TYPE) -> None:
        """ Validates custom config items.

        This is intended to be overriden by the user.
        """
        pass



    def print_config(self) -> None:
        print('Config contents: ')
        for key in self.config.keys():
            if key == 'dialect':
                print('    dialect:')
                for item in [x for x in vars(self.config[key]) if not x.startswith('_')]:
                    if item == 'quoting':
                        print(f'        {item}:  {getattr(self.config[key], item)}')
                        print(f'        {item}(translated):  {csvhelper.get_quote_name(getattr(self.config[key], item)) if self.config[key].quoting is not None else None}')
                    else:
                        print(f'        {item}:  {getattr(self.config[key], item)}')
            elif key == 'out_dialect':
                print('    out_dialect:')
                for item in [x for x in vars(self.config[key]) if not x.startswith('_')]:
                    print(f'        {item}:  {getattr(self.config[key], item)}')
            else:
                print(f'    {key}:  {self.config[key]}')
        print(' ')




class _EnvironmentalArgs(object):
    """ Manages all environmental configuration arguments related to the gristle app

        This class will collect these arguments from the environment,
        format them,
        then provide them via class attributes:
           self.env_gristle_app_args
    """

    def __init__(self,
                 gristle_app_name: str,
                 app_config: METADATA_TYPE) -> None:

        self.gristle_app_name = gristle_app_name
        self._app_metadata = app_config
        self.env_args = os.environ.items()
        self.env_gristle_app_args = self._get_gristle_app_args()

    def _get_gristle_app_args(self) -> CONFIG_TYPE:
        """ Returns a dictionary of environment keys & vals associated with the calling program.

        Note that the vals will be converted to the appropriate type.
        """
        env_config = {}
        for envkey, envval in sorted(self.env_args):
            if envkey in self._transform_config_keys_to_env_keys():
                option_name = self._transform_env_key_to_option_name(envkey)
                if self._app_metadata[option_name]['type'] is bool:
                    if self._app_metadata[option_name].get('dest', option_name) == option_name:
                        # issue: assumes env true/false matches app_config 'store_true'/'store_false'
                        env_config[option_name] = self._app_metadata[option_name]['type'](envval)
                    else:
                        pass # ignore booleans used to reverse a different boolean
                else:
                    env_config[option_name] = self._app_metadata[option_name]['type'](envval)
        return env_config

    def _transform_config_keys_to_env_keys(self):
        """ Translates the configuration keys to the env key formats by adding
            'gristle_[app_name] as a prefix to each key.
        """
        env_keys = [f'{self.gristle_app_name}_{key}' for key in self._app_metadata.keys()]
        return env_keys

    def _transform_env_key_to_option_name(self,
                                          envkey: str) -> str:
        """ Translates environment key to our option name format by stripping
            'gristle_[app_name]_' from the front of the env key
        """
        option_name = envkey[len(f'{self.gristle_app_name}_'):]
        return option_name



class _FileArgs(object):
    """ Manages all file-based configuration arguments related to the gristle app

        This class will collect these arguments from a config file,
        format them,
        then provide them via class attributes:
           self.file_gristle_app_args

        Notes on processing:
            1. Any dashes in keys within the config file are converted to underscores.
               This is consistent with how _CommandLineArgs() works - but inconsistent
               with how _EnvironmentalArgs() works (envvars can't have dashes). 
            2. Any relative paths will be in relationship to the directory that the
               config file is within.  This applies to the following path keys:
                   a.  infiles
                   b.  outfile
                   c.  outfiles
                   d.  outdir
                   e.  tmpdir
    """

    def __init__(self,
                 config_fn: str) -> None:

        if not isfile(config_fn):
            comm.abort(f'Error: config file not found!',
                       f'for config-fn: {config_fn}')
        self.config_fn = config_fn
        self.file_gristle_app_args = self._get_args()


    def _get_args(self) -> CONFIG_TYPE:
        """ Returns a dictionary of config keys & vals associated with the calling program.
        """
        file_args = {}

        if not self.config_fn:
            return file_args

        _, file_ext = os.path.splitext(self.config_fn)
        if file_ext in ('.yaml', '.yml'):
            with open(self.config_fn) as buf:
                file_args = yaml.safe_load(buf)
        elif file_ext in ('.json'):
            with open(self.config_fn) as buf:
                file_args = json.load(buf)

        self._convert_arg_name_delimiter(file_args)
        self._convert_file_path('infiles', file_args)
        self._convert_file_path('outfile', file_args)
        self._convert_file_path('outfiles', file_args)
        self._convert_file_path('outdir', file_args)
        self._convert_file_path('tmpdir', file_args)
        return file_args


    def _convert_file_path(self, path_key, args):
        """ Turn relative paths in config files into absolute paths

        The purpose of this is to support relative file paths - in particular
        for datagristle script cmdline testing.  In this case we need to have
        configs hold file names, but their absolute location would depend on
        where one clones the repo.

        The way this works is that any non-absolute file name in the config
        will be joined to the absolute directory of the config file itself.

        For users that want to take advantage of this they just need to be
        aware that the filename in the config is relative in comparison
        to the config directory itself.
        """
        if path_key not in args:
            return

        if type(args[path_key]) == type(['foo']):
            if args[path_key] == ['-']:
                return
            old_files = args[path_key]
            new_files = []
            config_dir = dirname(abspath(self.config_fn))
            for file in old_files:
                if isabs(file):
                    new_files.append(file)
                else:
                    new_file = pjoin(config_dir, file)
                    new_files.append(new_file)
            args[path_key] = new_files
        else:
            if args[path_key] == '-':
                return
            old_file = args[path_key]
            new_file = ''
            config_dir = dirname(abspath(self.config_fn))
            if isabs(old_file):
                new_file = old_file
            else:
                new_file = pjoin(config_dir, old_file)
            args[path_key] = new_file


    def _convert_arg_name_delimiter(self, args):
        """Replaces dashes in keys with underscores

        This is performed in order to change from the external standard of
        snake case (ex: foo-bar) to the internal standard of flattened snake case (ex: foo_bar).
        """
        for old_key in list(args.keys()):
            if '-' in old_key:
                new_key = old_key.replace('-', '_')
                args[new_key] = args[old_key]
                args.pop(old_key)



class _CommandLineArgs(object):

    def __init__(self,
                 short_help,
                 long_help,
                 app_metadata: str,
                 obsolete_args: Dict[str, str]={})-> None:

        self._app_metadata = app_metadata
        self.short_help = short_help
        self.long_help = long_help
        self.obsolete_args = obsolete_args
        self.cli_args = self._get_args(short_help)


    def _get_args(self,
                  desc: str) -> CONFIG_TYPE:
        """ Gets config items from cli arguments.
        """
        self._build_parser(desc)
        known_args, unknown_args = self.parser.parse_known_args()
        self._process_unknown_args(unknown_args)
        self._process_help_args(known_args)
        return vars(known_args)


    def _build_parser(self,
                      desc) -> None:

        #fixme: can only handle 1 positional argument: it doesn't actually have 'position' for positionals
        #This isn't a big problem since we're only using options - in order to also support envvars and 
        #config files
        self.parser = argparse.ArgumentParser(description=desc,
                                              usage='%(prog)s --long-help for detailed usage and help',
                                              add_help=False)

        self.parser.add_argument('--long-help',
                                 action='store_true',
                                 default=False,
                                 help='Print more verbose help')

        for key in self._app_metadata:
            self._add_argument_from_metadata(key)

        self.parser.add_argument('-V', '--version',
                                 action='store_true',
                                 default=False,
                                 help='show version number then exit')


    def _add_argument_from_metadata(self, key):
        args = []
        kwargs = {}

        long_name = (f'--{key}' if self._app_metadata[key]['arg_type'] == 'option' else key).replace('_', '-')
        skey = self._convert_arg_name_delimiter(self._app_metadata[key].get('short_name', ''))
        short_name = f'-{skey}'

        if skey:
            args.append(short_name)
        args.append(long_name)

        if 'nargs' in self._app_metadata[key]:
            kwargs['nargs'] = self._app_metadata[key]['nargs']

        kwargs['help'] = self._app_metadata[key]['help']

        if self._app_metadata[key]['type'] is bool:
            if 'action' in self._app_metadata[key]:
                kwargs['action'] = self._app_metadata[key]['action']
                if self._app_metadata[key].get('const') is not None:
                    kwargs['const'] = self._app_metadata[key]['const']
                if self._app_metadata[key]['action'] == 'store_true':
                    kwargs['const'] = True
            if 'dest' in self._app_metadata[key]:
                kwargs['dest'] = self._app_metadata[key]['dest']
        elif self._app_metadata[key]['type'] is list: # list is redundant with nargs and causes nesting
            pass
        else:
            kwargs['type'] = self._app_metadata[key]['type'] # don't include type for booleans
        self.parser.add_argument(*args, **kwargs)


    def _convert_arg_name_delimiter(self, arg_name: str) -> None:
        return arg_name.replace('_', '-')


    def _process_unknown_args(self, unknown_args: list) -> None:
        for arg in unknown_args:
            if arg in self.obsolete_args.keys():
                comm.abort('Error: obsolete option', self.obsolete_args[arg])
            else:
                comm.abort(f'ERROR: Unknown option: {arg}')


    def _process_help_args(self, known_args: list) -> None:
        if known_args.help:
            print(self.short_help)
            sys.exit(0)
        if known_args.long_help:
            print(self.long_help)
            sys.exit(0)
        if known_args.version:
            print(__version__)
            sys.exit(0)


