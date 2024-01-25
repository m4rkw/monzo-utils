from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.lib.monzo_sync import MonzoSync
from monzo_utils.lib.monzo_api import MonzoAPI
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError
import pytest
import os
import pwd
import datetime
from freezegun import freeze_time

class TestMonzoSync(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}


    @patch('os.path.exists')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_provider')
    @patch('monzo_utils.lib.config.Config.__init__')
    def test_constructor_init(self, mock_init_config, mock_get_provider, mock_db, mock_api, mock_exists):
        mock_init_config.return_value = None
        mock_exists.return_value = True
        mock_api.return_value = None
        mock_db.return_value = None
        mock_get_provider.return_value = 'provider'

        config = Config()
        Config._instances[Config] = config

        ms = MonzoSync()

        homedir = pwd.getpwuid(os.getuid()).pw_dir

        self.assertEqual(ms.monzo_dir, f"{homedir}/.monzo")
        self.assertEqual(ms.config_file, f"{homedir}/.monzo/config.yaml")
        self.assertEqual(ms.token_file, f"{homedir}/.monzo/tokens")

        self.assertIsInstance(ms.api, MonzoAPI)
        self.assertIsInstance(ms.db, DB)
        self.assertEqual(ms.provider, 'provider')


    @patch('os.path.exists')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_provider')
    @patch('monzo_utils.lib.config.Config.__init__')
    def test_constructor_no_init(self, mock_init_config, mock_get_provider, mock_db, mock_api, mock_exists):
        mock_init_config.return_value = None
        mock_exists.return_value = True
        mock_api.return_value = None
        mock_db.return_value = None
        mock_get_provider.return_value = 'provider'

        config = Config()
        Config._instances[Config] = config

        ms = MonzoSync(True)

        homedir = pwd.getpwuid(os.getuid()).pw_dir

        self.assertEqual(ms.monzo_dir, f"{homedir}/.monzo")
        self.assertEqual(ms.config_file, f"{homedir}/.monzo/config.yaml")
        self.assertEqual(ms.token_file, f"{homedir}/.monzo/tokens")

        with pytest.raises(AttributeError):
            ms.api

        with pytest.raises(AttributeError):
            ms.db

        with pytest.raises(AttributeError):
            ms.provider
