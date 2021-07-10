#!/usr/bin/env python
""" Manages user config - arguments and environmental variables.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2020-2021 Ken Farmer

    Challenges:
    1. config files are hierarchical, args & envs are flat
    2. cli args and config keys have dashes, envvars have underscores
    3. some input is intended to be interactive-only - such as --version, --help, --long-help
"""

# type: ignore  # pylint: disable=no-member
import argparse
import collections
import copy
import json
import os
from os.path import isfile, splitext, basename, isabs, dirname, abspath, join as pjoin, exists
from pprint import pprint as pp
import sys
from typing import List, Dict, Any, Callable, Optional, NamedTuple, Tuple

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


# These describe the valid types of the properties of configs
VALID_CONFIG_PROP_TYPES: Dict[str, Any] = {}
VALID_CONFIG_PROP_TYPES['short_name'] = str
VALID_CONFIG_PROP_TYPES['required'] = bool
VALID_CONFIG_PROP_TYPES['nargs'] = str
VALID_CONFIG_PROP_TYPES['action'] = str
VALID_CONFIG_PROP_TYPES['const'] = bool
VALID_CONFIG_PROP_TYPES['choices'] = list
VALID_CONFIG_PROP_TYPES['min_length'] = int
VALID_CONFIG_PROP_TYPES['max_length'] = int
VALID_CONFIG_PROP_TYPES['minimum'] = int
VALID_CONFIG_PROP_TYPES['maximum'] = int
VALID_CONFIG_PROP_TYPES['dest'] = str
#NOT CHECKED BECAUSE they support multiple types or callbacks:
#VALID_METADATA_TYPEs['default'] = [str, int, float]
#VALID_METADATA_TYPEs['type'] = [str, int, float]
#VALID_METADATA_TYPEs['extended_default'] = [str, int, float]
#VALID_METADATA_TYPEs['transformer'] = None

VALID_CONFIG_PROP_VALUES = {}
VALID_CONFIG_PROP_VALUES['nargs'] = ['*', '?', '+']
VALID_CONFIG_PROP_VALUES['action'] = ['store_const', 'store_true', 'store_false']


STANDARD_CONFIGS: META_CONFIG_TYPE = {}
# IO Config Items:
STANDARD_CONFIGS['infiles'] = {'short_name': 'i',
                               'default': '-',
                               'required': True,
                               'type': str,
                               'nargs': '*'}
STANDARD_CONFIGS['outfile'] = {'short_name': 'o',
                               'default': '-',
                               'required': True,
                               'type': str}

# CSV Config Items:
STANDARD_CONFIGS['delimiter'] = {'short_name': 'd',
                                 'extended_default': ',',
                                 'type': str,
                                 'min_length': 1,
                                 'max_length': 1,
                                 'transformer': transform_delimiter}
STANDARD_CONFIGS['quoting'] = {'short_name': 'q',
                               'extended_default': 'quote_none',
                               'choices': ['quote_all', 'quote_minimal',
                                           'quote_nonnumeric', 'quote_none'],
                               'type': str,
                               'transformer': transform_lower}
STANDARD_CONFIGS['quotechar'] = {'extended_default': '"',
                                 'type': str,
                                 'min_length': 1,
                                 'max_length': 1}
STANDARD_CONFIGS['escapechar'] = {'type': str,
                                  'extended_default': None}
STANDARD_CONFIGS['doublequote'] = {'type': bool,
                                   'action': 'store_const',
                                   'const': True,
                                   'extended_default': False}
STANDARD_CONFIGS['no_doublequote'] = {'type': bool,
                                      'action': 'store_const',
                                      'const': False,
                                      'dest': 'doublequote'}
STANDARD_CONFIGS['has_header'] = {'type': bool,
                                  'action': 'store_const',
                                  'const': True,
                                  'extended_default': False}
STANDARD_CONFIGS['has_no_header'] = {'type': bool,
                                     'action': 'store_const',
                                     'const': False,
                                     'dest': 'has_header'}
STANDARD_CONFIGS['skipinitialspace'] = {'type': bool,
                                        'action': 'store_const',
                                        'const': True,
                                        'extended_default': False}
STANDARD_CONFIGS['no-skipinitialspace'] = {'type': bool,
                                           'dest': 'skipinitialspace',
                                           'action': 'store_const',
                                           'const': False}


# Misc Config Items:
STANDARD_CONFIGS['verbosity'] = {'default': 'normal',
                                 'type': str,
                                 'choices': ['quiet', 'normal', 'high', 'debug'] }

STANDARD_CONFIGS['dry_run'] = {'default': False,
                               'type': bool,
                               'action': 'store_const',
                               'const': True}

STANDARD_CONFIGS['config_fn'] = {'default': None,
                                 'type': str}
STANDARD_CONFIGS['gen_config_fn'] = {'default': None,
                                     'type': str}

STANDARD_CONFIGS['help'] = {'short_name': 'h',
                            'default': None,
                            'type': bool,
                            'action': 'store_true'}


ARG_ONLY_CONFIGS = ['version', 'long_help', 'config_fn', 'long-help']



class Config(object):

    class NConfig(NamedTuple):   # type: ignore  # pylint: disable=no-member
        """ Bare minimum nconfig for typing
        """
        verbosity: str


    def __init__(self,
                 app_name: str,
                 short_help: str,
                 long_help: str) -> None:

        self.app_name = splitext(basename(app_name))[0]
        self.short_help = short_help
        self.long_help = long_help
        self.obsolete_options: Dict[str, Any] = {}
        self._app_metadata: META_CONFIG_TYPE = {}
        self.config: Dict = {}
        self.nconfig = self.NConfig


    def extend_config(self):
        """ Provide calling programs function placeholder for add-ons

        This function exists so that additional attributes beyond what were picked up from
        cli, config file, or envvar can be added to the config.  These might be derived from
        the config, or wholly new.
        """
        pass


    def define_user_config(self):
        """ Provide calling programs function placeholder for defining config

        This is where the calling program defines all config items.
        """
        pass


    def define_obsolete_config(self):
        """ Provide calling programs function placeholder for defining obsolete config

        This is where the calling program defines all obsolete config items.
        """
        pass


    def get_config(self) -> Tuple[Any, Dict[Any, Any]]:
        self.define_user_config()
        self.define_obsolete_config()
        self.process_configs()

        self.extend_config()

        if self.nconfig.verbosity == 'debug':
            self.print_config(key='dialect')

        return self.nconfig, self.config


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

        if self._app_metadata[name]['type'] == 'bool':
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
        self.add_standard_metadata('skipinitialspace')
        self.add_standard_metadata('no-skipinitialspace')


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

        self._validate_config_metadata()

        # Get inputs from all three interfaces:
        env_args_manager = _EnvironmentalArgs(self.app_name, self._app_metadata)
        env_args = env_args_manager.env_gristle_app_args

        cli_args_manager = _CommandLineArgs(self.short_help, self.long_help, self._app_metadata, self.obsolete_options)
        cli_args_manager._get_args()
        cli_args = cli_args_manager.cli_args

        config_fn = cli_args.get('config_fn', None) or env_args.get('config_fn', None)
        if config_fn:
            file_args_manager = _FileArgs(config_fn, self._app_metadata)
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
        with open(self.nconfig.gen_config_fn, 'wt') as outbuf:  # pylint: disable=no-member
            if self.nconfig.gen_config_fn.endswith('.yml') or self.nconfig.gen_config_fn.endswith('.yaml'):
                filtered_config = {k:v for k,v in self.config.items() if k not in ARG_ONLY_CONFIGS}
                filtered_config = {k:v for k,v in filtered_config.items() if k != 'gen_config_fn'}
                yaml.dump(filtered_config, outbuf, indent=4, default_flow_style=False)
            elif self.nconfig.gen_config_fn.endswith('.json'):
                json.dump(self.config, outbuf)
            else:
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
        self.nconfig = collections.namedtuple('Config', self.config.keys())(**self.config)  # pylint: disable=no-member


    def update_config(self, key, value):
        """ Writes a key-value to the config.
        """
        new_config = {**self.config, **{key: value}}  # type: ignore  # pylint: disable=no-member
        self.replace_configs(new_config)


    def generate_csv_dialect_config(self):
        """ Adds the csv dialect to the config.

            Added by calling programs within the extend_config method.
        """
        md = self._app_metadata
        try:
            autodetected = csvhelper.get_dialect(infiles=self.config['infiles'],
                                                 verbosity=self.config['verbosity'])
        except FileNotFoundError:
            comm.abort('Error: File not found',
                       f"One of these files was not found: {','.join(self.config['infiles'])}")

        # First override auto-detected dialect with any explicit options
        overridden = csvhelper.override_dialect(autodetected,
                                                delimiter=self.config['delimiter'],
                                                quoting=self.config['quoting'],
                                                quotechar=self.config['quotechar'],
                                                has_header=self.config['has_header'],
                                                doublequote=self.config['doublequote'],
                                                escapechar=self.config['escapechar'],
                                                skipinitialspace=self.config['skipinitialspace'])

        # Finally we can apply any defaults needed - using the extended-defaults, which exist
        # because regular defaults would have been automatically applied.
        defaulted = csvhelper.default_dialect(overridden,
                                              delimiter=md['delimiter']['extended_default'],
                                              quoting=md['quoting']['extended_default'],
                                              has_header=md['has_header']['extended_default'],
                                              quotechar=md['quotechar']['extended_default'],
                                              escapechar=md['escapechar']['extended_default'],
                                              doublequote=md['doublequote']['extended_default'],
                                              skipinitialspace=md['skipinitialspace']['extended_default'])

        assert csvhelper.is_valid_dialect(defaulted)

        self.update_config('dialect', defaulted)


    def generate_csv_header_config(self):
        """ Adds the csv header to the config.

            Added by calling programs within the extend_config method.
        """

        header = csvhelper.Header()
        if self.config['infiles'][0] != '-':
            header.load_from_files(self.config['infiles'], self.config['dialect'])
        self.update_config('header', header)



    def _validate_config_metadata(self):
        """ Validates the program's configuration metadata (not the user's input).
        """
        for arg, arg_parameters in self._app_metadata.items():
            for property_name, property_value in arg_parameters.items():

                # Check the types of each parameter:
                if property_name in VALID_CONFIG_PROP_TYPES:
                    if type(property_value) is not VALID_CONFIG_PROP_TYPES[property_name]:
                        raise ValueError(f'{arg}.{property_name} type is invalid: {property_value}')

                # Check valid values:
                if property_name in VALID_CONFIG_PROP_VALUES:
                    if property_value not in VALID_CONFIG_PROP_VALUES[property_name]:
                        raise ValueError(f'{arg}.{property_name} value not one of valid choices')

                # Custom Validations:
                if property_name == 'short_name':
                    if len(property_value) != 1:
                        raise ValueError(f'{arg}.short_name length is invalid')

                if property_name == 'dest':
                    if property_value not in self._app_metadata:
                        raise ValueError(f'{arg}.dest refers to non-existing option')



    def _consolidate_configs(self,
                             file_args: CONFIG_TYPE,
                             env_args: CONFIG_TYPE,
                             cli_args: CONFIG_TYPE) -> CONFIG_TYPE:
        """ Consolidates environmental and cli arguments.

        First all _app_metadata keys are added,
        Then values from matching file, then env, then cli keys are overlaid
        """
        consolidated_args: Dict[str, Any] = {}

        def _get_actual_value(key, config_val):
            bool_val = None
            if key != self._app_metadata[key].get('dest', key):
                if (self._app_metadata[key]['type'] is bool
                        and self._app_metadata[key]['action'] == 'store_const'):
                    bool_val = self._app_metadata[key]['const']
                    return bool_val
            return config_val

        def _init_dictionary():
            for key in self._app_metadata:
                actual_key = self._app_metadata[key].get('dest', key)
                consolidated_args[actual_key] = None
            return consolidated_args

        def _add_file_args():
            for key, val in file_args.items():
                try:
                    actual_key = self._app_metadata[key].get('dest', key)
                    actual_val = _get_actual_value(key, val)
                    consolidated_args[actual_key] = actual_val
                except KeyError:
                    if key in self.obsolete_options.keys():
                        comm.abort('Error: obsolete option', self.obsolete_options[key])
                    else:
                        comm.abort(f'ERROR: Unknown option: {key}')
            return consolidated_args

        def _add_env_args():
            for key, val in env_args.items():
                actual_key = self._app_metadata[key].get('dest', key)
                consolidated_args[actual_key] = _get_actual_value(key, val)
            return consolidated_args

        def _add_cli_args():
            for key, val in cli_args.items():
                if val is not None and val != []:
                    consolidated_args[key] = val
            return consolidated_args

        consolidated_args = _init_dictionary()
        consolidated_args = _add_file_args()
        consolidated_args = _add_env_args()
        consolidated_args = _add_cli_args()

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
                    checks = self._app_metadata[key]

                    if not isinstance(val, checks['type']):
                        comm.abort('Error: config value has the wrong type',
                                   f"'{key}' with value: '{val}' is not {checks['type']}")

                    if 'min_length' in checks:
                        if len(val) < checks['min_length']:
                            comm.abort('Error: config value is under min_length',
                                       f"'{key}' with len of value '{val}' is < {checks['min_length']}")

                    if 'max_length' in checks:
                        if len(val) > checks['max_length']:
                            comm.abort("Error: config value is over max_length",
                                       f"'{key}' with len of value '{val}' is > {checks['max_length']}")

                    if 'minimum' in checks:
                        if val < checks['minimum']:
                            comm.abort(f"Error: config value less than minimum",
                                       f"'{key}' with value of '{val}' is < {checks['minimum']}")

                    if 'maximum' in checks:
                        if val > checks['maximum']:
                            comm.abort(f"Error: config value greater than maximum",
                                       f"'{key}' with value of '{val}' is > {checks['maximum']}")

                    if 'choices' in checks:
                        if val not in checks['choices']:
                            comm.abort(f"Error: config value not in valid list of choices",
                                       f"Valid values include: {checks['choices']} ")

        self._validate_dialect_with_stdin(config)


    def _validate_dialect_with_stdin(self, config) -> None:
        if config.get('infiles', '') == '-':
            if config['delimiter'] is None:
                comm.abort('Error: csv dialect delimiter is required when piping data via stdin')
            if config['quoting'] is None:
                comm.abort('Error: csv dialect quoting is required when piping data via stdin')
            if config['has_header'] is None:
                comm.abort('Error: csv dialect header info is required when piping via stdin')



    def validate_custom_config(self, config: CONFIG_TYPE) -> None:
        """ Validates custom config items.

        This is intended to be overriden by the user.
        """
        pass



    def print_config(self,
                     cli_args=None,
                     file_args=None,
                     env_args=None,
                     consolidated_args=None,
                     key=None) -> None:

        for a_key in self.config.keys():
            if key and key != a_key:
                continue
            if a_key == 'dialect':
                print('    dialect:')
                for item in [x for x in vars(self.config[a_key]) if not x.startswith('_')]:
                    if item == 'quoting':
                        print(f'        {item}:  {getattr(self.config[a_key], item)}')
                        if self.config[a_key].quoting is None:
                            quoting = None
                        else:
                            quoting = csvhelper.get_quote_name(getattr(self.config[a_key], item))
                        print(f'        {item}(translated):  {quoting}')
                    else:
                        print(f'        {item}:  {getattr(self.config[a_key], item)}')
            elif a_key == 'out_dialect':
                print('    out_dialect:')
                for item in [x for x in vars(self.config[a_key]) if not x.startswith('_')]:
                    print(f'        {item}:  {getattr(self.config[a_key], item)}')
            else:
                print(f'    {a_key}:  {self.config[a_key]}')

        if cli_args:
            print(' ')
            print('----------------------------------------------------')
            print('cli config: ')
            print('----------------------------------------------------')
            pp(cli_args)
        if file_args:
            print(' ')
            print('----------------------------------------------------')
            print('file config: ')
            print('----------------------------------------------------')
            pp(file_args)
        if env_args:
            print(' ')
            print('----------------------------------------------------')
            print('env config: ')
            print('----------------------------------------------------')
            pp(env_args)
        if consolidated_args:
            print(' ')
            print('----------------------------------------------------')
            print('consolidated config: ')
            print('----------------------------------------------------')
            pp(consolidated_args)




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
        self.app_metadata = app_config
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
                env_config[option_name] = self.app_metadata[option_name]['type'](envval)
        env_config_binaries_cleaned = binary_arg_fixer(self.app_metadata, env_config)
        return env_config_binaries_cleaned

    def _transform_config_keys_to_env_keys(self):
        """ Translates the configuration keys to the env key formats by adding
            'gristle_[app_name] as a prefix to each key.
        """
        env_keys = [f'{self.gristle_app_name}_{key}' for key in self.app_metadata.keys()]
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

        This class will collect these arguments from a config file, format them,
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
            3. Any keys that are binaries will be validated to ensure they evaluate
               to true, and then their const values will be applied to their
               destinations.
    """

    def __init__(self,
                 config_fn: str,
                 app_metadata) -> None:

        if not isfile(config_fn):
            comm.abort(f'Error: config file not found!',
                       f'for config-fn: {config_fn}')
        self.config_fn = config_fn
        self.app_metadata = app_metadata
        self.file_gristle_app_args = self._get_args()


    def _get_args(self) -> CONFIG_TYPE:
        """ Returns a dictionary of config keys & vals associated with the calling program.
        """
        file_args: Dict[str, Any] = {}

        if not self.config_fn:
            return file_args

        _, file_ext = os.path.splitext(self.config_fn)
        if file_ext in ('.yaml', '.yml'):
            with open(self.config_fn) as buf:
                file_args = yaml.safe_load(buf)
        elif file_ext in ('.json'):
            with open(self.config_fn) as buf:
                file_args = json.load(buf)

        file_args_binaries_cleaned = binary_arg_fixer(self.app_metadata, file_args)
        file_args_final = self.file_args_path_cleaner(file_args_binaries_cleaned)
        return file_args_final


    def file_args_path_cleaner(self,
                               file_args):

        output_args = copy.deepcopy(file_args)

        self._convert_arg_name_delimiter(output_args)
        self._convert_file_path('infiles', output_args)
        self._convert_file_path('outfile', output_args)
        self._convert_file_path('outfiles', output_args)
        self._convert_file_path('outdir', output_args)
        self._convert_file_path('out_dir', output_args)
        self._convert_file_path('tmpdir', output_args)
        self._convert_file_path('source_dir', output_args)
        self._convert_file_path('dest_dir', output_args)
        return output_args


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

        config_dir = dirname(abspath(self.config_fn))
        if type(args[path_key]) == type(['foo']):
            if args[path_key] == ['-']:
                return
            old_files = args[path_key]
            new_files = []
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
                 app_metadata: META_CONFIG_TYPE,
                 obsolete_options: Dict[str, str] = None)-> None:

        self._app_metadata = app_metadata
        self.short_help = short_help
        self.long_help = long_help
        self.obsolete_options = obsolete_options or {}
        self.cli_args = self._get_args()


    def _get_args(self) -> CONFIG_TYPE:
        """ Gets config items from cli arguments.
        """
        self._build_parser()
        known_args, unknown_args = self.parser.parse_known_args()
        self._process_unknown_args(unknown_args)
        self._process_help_args(known_args)
        return vars(known_args)


    def _build_parser(self) -> None:

        #fixme: can only handle 1 positional argument: it doesn't actually have 'position' for positionals
        #This isn't a big problem since we're only using options - in order to also support envvars and
        #config files
        self.parser = argparse.ArgumentParser(usage = '%(prog)s --long-help for detailed usage and help',
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

        long_name = f'--{key}'.replace('_', '-')
        skey = self._convert_arg_name_delimiter(self._app_metadata[key].get('short_name', ''))
        short_name = f'-{skey}'

        if skey:
            args.append(short_name)
        args.append(long_name)

        if 'nargs' in self._app_metadata[key]:
            kwargs['nargs'] = self._app_metadata[key]['nargs']

        if self._app_metadata[key]['type'] is bool:
            if 'action' in self._app_metadata[key]:
                kwargs['action'] = self._app_metadata[key]['action']
                if self._app_metadata[key].get('const') is not None:
                    kwargs['const'] = self._app_metadata[key]['const']
            if 'dest' in self._app_metadata[key]:
                kwargs['dest'] = self._app_metadata[key]['dest']
        elif self._app_metadata[key]['type'] is list: # list is redundant with nargs and causes nesting
            pass
        else:
            kwargs['type'] = self._app_metadata[key]['type'] # don't include type for booleans
        self.parser.add_argument(*args, **kwargs)


    def _convert_arg_name_delimiter(self, arg_name: str) -> str:
        return arg_name.replace('_', '-')


    def _process_unknown_args(self, unknown_args: list) -> None:
        for arg in unknown_args:
            if arg in self.obsolete_options.keys():
                comm.abort('Error: obsolete option', self.obsolete_options[arg])
            else:
                comm.abort(f'ERROR: Unknown option: {arg}')


    def _process_help_args(self,
                           known_args: argparse.Namespace) -> None:
        if known_args.help:
            print(self.short_help)
            sys.exit(0)
        if known_args.long_help:
            print(self.long_help)
            sys.exit(0)
        if known_args.version:
            print(__version__)
            sys.exit(0)



def binary_arg_fixer(app_metadata,
                     args):
    """ Returns a copy of the args in which:
        - keys are replaced by any destination key names if they exist
        - and store_const is used rather than value for bools

        The reason for this function is that unlike cli args, envvars
        and config files don't have flags whose mere existance indicates
        True or False: instead config files have bools which can be set
        either way and envvars just have strings - which might have a True
        or False, 1 or 0.  This code helps treat the envvars & config files
        like cli args.
    """

    def get_bool_actual_value(key,
                              orig_config_val):
        assert app_metadata[key]['type'] is bool
        assert app_metadata[key]['action'] == 'store_const'
        assert app_metadata[key]['const'] in (True, False)

        if type(orig_config_val) is bool:
            transformed_config_val = orig_config_val
        elif orig_config_val is None or orig_config_val.strip().lower() in ('none', 'null'):
            comm.abort(f'Config item {key} has a non-true value of {orig_config_val}',
                       'This is a flag type whose value is established by pgm metadata '
                       'and when provided via envvar or config file must always be set to true')
        else:
            transformed_config_val = orig_config_val.strip().lower() in ('true', 't', '1', '')

        if not transformed_config_val:
            comm.abort(f'Config item {key} has a non-true value of {orig_config_val}',
                       'This is a flag type whose value is established by pgm metadata'
                       'and when provided via envvar or config file must always be set to true')

        return app_metadata[key]['const']

    cleaned_args = {}
    for orig_key, val in args.items():
        try:
            if app_metadata[orig_key]['type'] != bool:
                cleaned_args[orig_key] = val
            else:
                actual_key = app_metadata[orig_key].get('dest', orig_key)
                actual_val = get_bool_actual_value(orig_key, val)
                cleaned_args[actual_key] = actual_val
        except KeyError:
            comm.abort(f'Error: option {orig_key} is unknown')

    return cleaned_args



