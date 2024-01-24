from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from monzo_utils.lib.config import Config
from monzo_utils.lib.db import DB
import os
import pwd

class TestConfig(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}

    @patch('os.path.exists')
    @patch('monzo_utils.lib.config.Config.get_file_contents')
    @patch('yaml.safe_load')
    @patch('os.mkdir')
    def test_init_make_config_dir(self, mock_mkdir, mock_yaml_load, mock_get_file_contents, mock_exists):
        mock_exists.side_effect = [False, True]

        Config(None, '/tmp/config_path')

        mock_mkdir.assert_called_with('/tmp/config_path', 0o755)


    @patch('os.path.exists')
    def test_init_set_config(self, mock_exists):
        mock_exists.return_value = True

        config = Config({"key": "config1"})

        self.assertEqual(config.config, {"key": "config1"})


    @patch('os.path.exists')
    @patch('monzo_utils.lib.config.Config.get_file_contents')
    @patch('yaml.safe_load')
    @patch('os.mkdir')
    def test_init_config_from_file(self, mock_mkdir, mock_yaml_load, mock_get_file_contents, mock_exists):
        mock_exists.side_effect = [True, True]

        mock_get_file_contents.return_value = 'file content'
        mock_yaml_load.return_value = {"key": "config1"}

        config = Config(None, '/tmp/config_path')

        mock_get_file_contents.assert_called_with('/tmp/config_path/config.yaml')
        mock_yaml_load.assert_called_with('file content')

        self.assertEqual(config.config, {"key": "config1"})


    @patch('os.path.exists')
    def test_getattr(self, mock_exists):
        mock_exists.return_value = True

        config = Config({
                "key": "config1",
                "key2": "config2"
        })

        self.assertEqual(config.key, "config1")
        self.assertEqual(config.key2, "config2")


    @patch('os.path.exists')
    def test_set(self, mock_exists):
        mock_exists.return_value = True

        config = Config({
                "key": "config1",
                "key2": "config2"
        })

        config.set('key3', 'blah')

        self.assertEqual(config.key, "config1")
        self.assertEqual(config.key2, "config2")
        self.assertEqual(config.key3, "blah")


    @patch('os.path.exists')
    def test_keys(self, mock_exists):
        mock_exists.return_value = True

        config = Config({
                "key": "config1",
                "key2": "config2"
        })

        config.set('key3', 'blah')

        self.assertEqual(list(sorted(config.keys)), ['key','key2','key3'])


    @patch('os.path.exists')
    @patch('monzo_utils.lib.config.Config.set_file_contents')
    def test_save(self, mock_file_write, mock_exists):
        mock_exists.return_value = True

        config = Config({
                "key": "config1",
                "key2": "config2"
        })

        config.set('key3', 'blah')

        config.save()

        homedir = pwd.getpwuid(os.getuid()).pw_dir

        mock_file_write.assert_called_with(f'{homedir}/.monzo/config.yaml', 'key: config1\nkey2: config2\nkey3: blah\n')
