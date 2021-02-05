#!/usr/bin/env python
#todo: add testing for cli args

import json
import os
from os.path import join as pjoin
from pprint import pprint as pp
import shutil
import tempfile

import datagristle.configulator as mod


GRISTLE_APP_NAME = 'gristle_fooper'
PGM_NAME = '/tmp/gristle_fooper.py'
SHORT_HELP = 'gristle_fooper short-help'
LONG_HELP = 'gristle_fooper long-help'




class TestEnvironmentalArgs(object):

    def setup_method(self, method):

        # setup _app_metadata:
        config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        config.add_custom_metadata(name='delimiter',
                                   config_type=str,
                                   arg_type='option',
                                   default=None,
                                   help_msg=SHORT_HELP)
        config.add_custom_metadata(name='counter',
                                   config_type=int,
                                   arg_type='option',
                                   default=None,
                                   help_msg=SHORT_HELP)
        self._app_metadata = config._app_metadata
        pp(self._app_metadata)

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

        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self._app_metadata)
        env_config = env_args._get_gristle_app_args()
        assert env_config == {}


    def test_simple_environment_variable(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_delimiter'] = '$'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self._app_metadata)
        env_config = env_args._get_gristle_app_args()
        pp(env_config)
        assert env_config['delimiter'] == '$'


    def test_type_converted_environment_variable(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_counter'] = '999'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self._app_metadata)
        env_config = env_args._get_gristle_app_args()
        pp(env_config)
        assert env_config['counter'] == 999




class TestFileArgs(object):

    def setup_method(self, method):

        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

        # setup app_config:
        config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        config.add_custom_metadata(name='delimiter',
                                   config_type=str,
                                   arg_type='option',
                                   default=None,
                                   help_msg=SHORT_HELP)
        config.add_custom_metadata(name='counter',
                                   config_type=int,
                                   arg_type='option',
                                   default=None,
                                   help_msg=SHORT_HELP)
        config.add_standard_metadata('config_fn')
        self._app_metadata = config._app_metadata
        pp(self._app_metadata)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_empty_file_arguments(self):

        config_dict_to_write = {}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)


        file_args = mod._FileArgs(self.config_fqfn)
        assert file_args.file_gristle_app_args == {}


    def test_simple_file_arguments(self):

        config_dict_to_write = {'delimiter': '$',
                                'counter': 999}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        self._app_metadata['config-fn'] = self.config_fqfn
        file_args = mod._FileArgs(self.config_fqfn)
        assert file_args.file_gristle_app_args == config_dict_to_write


    def test_nested_file_argument(self):

        config_dict_to_write = {'delimiter': '$',
                                'counter': 999,
                                'assignments':
                                    [ {'foo': 1,
                                       'bar': 'a'},
                                      {'foo': 2,
                                       'bar': 'b'}
                                    ]
                                }
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        self._app_metadata['config-fn'] = self.config_fqfn
        file_args = mod._FileArgs(self.config_fqfn)
        assert file_args.file_gristle_app_args == config_dict_to_write


def create_config_file(temp_dir, config_dict):
    with open(pjoin(temp_dir, 'config_file.json'), 'w') as outbuf:
        json.dump(config_dict, outbuf)
    return pjoin(temp_dir, 'config_file.json')






