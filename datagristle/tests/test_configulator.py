#!/usr/bin/env python
#todo: add testing for cli args

import json
import os
from os.path import join as pjoin
from pprint import pprint as pp
import shutil
import tempfile

import pytest

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
                                   type=str,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        config.add_custom_metadata(name='counter',
                                   type=int,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        config.add_standard_metadata('has_header')
        config.add_standard_metadata('has_no_header')

        self._app_metadata = config._app_metadata
        pp(self._app_metadata)


    def teardown_method(self, method):
        try:
            os.environ.pop(f'{GRISTLE_APP_NAME}_delimiter')
            os.environ.pop(f'{GRISTLE_APP_NAME}_counter')
            os.environ.pop(f'{GRISTLE_APP_NAME}_has_header')
            os.environ.pop(f'{GRISTLE_APP_NAME}_has_no_header')
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


    def test_boolean_has_header(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_has_header'] = 'true'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self._app_metadata)
        env_config = env_args._get_gristle_app_args()
        pp(env_config)
        assert env_config['has_header'] is True


    def test_reverse_boolean_has_no_header(self):

        # export arg into environment:
        os.environ[f'{GRISTLE_APP_NAME}_has_no_header'] = 'true'

        # now confirm environment args produce an good results:
        env_args = mod._EnvironmentalArgs(GRISTLE_APP_NAME, self._app_metadata)
        env_config = env_args._get_gristle_app_args()
        assert env_config['has_header'] is False




class TestFileArgs(object):

    def setup_method(self, method):

        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

        # setup app_config:
        config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        config.add_custom_metadata(name='delimiter',
                                   type=str,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        config.add_custom_metadata(name='counter',
                                   type=int,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        config.add_custom_metadata(name='assignments',
                                   type=list,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        config.add_standard_metadata('config_fn')
        config.add_standard_metadata('has_header')
        config.add_standard_metadata('has_no_header')
        self._app_metadata = config._app_metadata
        pp(self._app_metadata)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_empty_file_arguments(self):

        config_dict_to_write = {}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        file_args = mod._FileArgs(self.config_fqfn, self._app_metadata)
        assert file_args.file_gristle_app_args == {}


    def test_simple_file_arguments(self):

        config_dict_to_write = {'delimiter': '$',
                                'counter': 999}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        self._app_metadata['config-fn'] = self.config_fqfn
        file_args = mod._FileArgs(self.config_fqfn, self._app_metadata)
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
        file_args = mod._FileArgs(self.config_fqfn, self._app_metadata)
        assert file_args.file_gristle_app_args == config_dict_to_write


    def test_boolean_has_header(self):

        config_dict_to_write = {'has_header': True}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        self._app_metadata['config-fn'] = self.config_fqfn
        file_args = mod._FileArgs(self.config_fqfn, self._app_metadata)
        assert file_args.file_gristle_app_args == config_dict_to_write


    def test_reverse_boolean_has_header(self):

        config_dict_to_write = {'has_no_header': True}
        self.config_fqfn = create_config_file(self.temp_dir, config_dict_to_write)
        self._app_metadata['config-fn'] = self.config_fqfn
        file_args = mod._FileArgs(self.config_fqfn, self._app_metadata)
        #assert file_args.file_gristle_app_args == {'has_no_header': True}
        assert file_args.file_gristle_app_args == {'has_header': False}


# need to test consolidation!

# need to test cli

def create_config_file(temp_dir, config_dict):
    with open(pjoin(temp_dir, 'config_file.json'), 'w') as outbuf:
        json.dump(config_dict, outbuf)
    return pjoin(temp_dir, 'config_file.json')




class TestBinaryArgFixer(object):

    def setup_method(self, method):

        self.temp_dir = tempfile.mkdtemp(prefix='gristle_test_')

        # setup app_config:
        self.config = mod.Config(PGM_NAME, SHORT_HELP, LONG_HELP)
        self.config.add_custom_metadata(name='delimiter',
                                   type=str,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        self.config.add_custom_metadata(name='counter',
                                   type=int,
                                   arg_type='option',
                                   default=None,
                                   help=SHORT_HELP)
        self.config.add_standard_metadata('config_fn')
        self.config.add_standard_metadata('has_header')
        self.config.add_standard_metadata('has_no_header')
        self._app_metadata = self.config._app_metadata
        pp(self._app_metadata)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)


    def test_empty_args(self):

        test_config = {}
        assert mod.binary_arg_fixer(self._app_metadata, test_config) == {}


    def test_bool_true_args(self):

        test_config = {}
        test_config['has_header'] = 'true'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = 'True'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = 'TRUE'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = '1'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = 't'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = 'T'
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True

        test_config['has_header'] = ''
        resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)
        assert resulting_args['has_header'] == True


    def test_bool_false_args(self):

        test_config = {}
        test_config['has_header'] = 'false'
        with pytest.raises(SystemExit):
            resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)

        test_config = {}
        test_config['has_header'] = '0'
        with pytest.raises(SystemExit):
            resulting_args = mod.binary_arg_fixer(self._app_metadata, test_config)



