from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.lib.monzo_sync import MonzoSync
from monzo_utils.lib.monzo_api import MonzoAPI
from monzo_utils.model.account import Account
from monzo_utils.model.merchant import Merchant
from monzo_utils.model.merchant_address import MerchantAddress
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError
import monzo.endpoints.account
import monzo.endpoints.balance
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


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.config.Config.save')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo.endpoints.account.Account.__init__')
    @patch('monzo.endpoints.balance.Balance.__init__')
    @patch('builtins.print')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.prompt_input')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.prompt_continue')
    def test_scan_accounts(self, mock_prompt_continue, mock_prompt_input, mock_print, mock_init_balance, mock_init_account, mock_init, mock_save_config, mock_db):
        mock_init_balance.return_value = None
        mock_init_account.return_value = None
        mock_init.return_value = None
        mock_db.return_value = None

        config = Config({
            'accounts': {}
        })

        Config._instances[Config] = config

        balance1 = monzo.endpoints.balance.Balance()
        balance1._balance = 123

        account1 = monzo.endpoints.account.Account()
        account1._account_id = 123
        account1._balance = balance1
        account1._description = 'test'

        balance2 = monzo.endpoints.balance.Balance()
        balance2._balance = 123

        account2 = monzo.endpoints.account.Account()
        account2._account_id = 123
        account2._balance = balance2
        account2._description = 'test'

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.accounts.return_value = [account1, account2]

        ms.scan_accounts()


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    def test_test_db_access_mysql(self, mock_init, mock_query, mock_db_init):
        mock_init.return_value = None
        mock_db_init.return_value = None

        ms = MonzoSync()

        ms.test_db_access({
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'test'
        })

        mock_db_init.assert_called_with({
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'test'
        })

        mock_query.assert_called_with('show tables')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    def test_test_db_access_sqlite(self, mock_init, mock_query, mock_db_init):
        mock_init.return_value = None
        mock_db_init.return_value = None

        ms = MonzoSync()

        ms.test_db_access({
            'driver': 'sqlite3',
            'host': 'localhost',
            'database': 'test'
        })

        mock_db_init.assert_called_with({
            'driver': 'sqlite3',
            'host': 'localhost',
            'database': 'test'
        })

        mock_query.assert_called_with('pragma table_info(`provider`)')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.merchant.Merchant.one')
    @patch('monzo_utils.model.merchant.Merchant.update')
    @patch('monzo_utils.model.merchant.Merchant.save')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.one')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.update')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.save')
    @patch('monzo_utils.model.merchant.Merchant.__init__')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.__init__')
    def test_get_or_create_merchant_create(self, mock_merchant_address_init, mock_init_merchant, mock_merchant_address_save, mock_merchant_address_update, mock_merchant_address_one, mock_merchant_save, mock_merchant_update, mock_merchant_one, mock_init, mock_query, mock_db_init):
        mock_init.return_value = None
        mock_db_init.return_value = None
        mock_init_merchant.return_value = None
        mock_merchant_address_init.return_value = None

        mock_merchant_one.return_value = None

        mock_merchant_address_one.return_value = None

        ms = MonzoSync()

        mo_merchant = {
            'id': 'werjoidsf',
            'name': 'test',
            'address': {
            }
        }

        merch = ms.get_or_create_merchant(mo_merchant)

        mock_merchant_one.assert_called_with('select * from merchant where merchant_id = %s', ['werjoidsf'])

        mock_init_merchant.assert_called_with()
        mock_merchant_save.assert_called_with()
        mock_merchant_update.assert_called_with({'name': 'test', 'merchant_id': 'werjoidsf'})

        self.assertEqual(merch.id, None)

        mock_merchant_address_init.assert_called_with()
        mock_merchant_address_save.assert_called_with()
        mock_merchant_address_update.assert_called_with({'merchant_id': None})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.merchant.Merchant.one')
    @patch('monzo_utils.model.merchant.Merchant.update')
    @patch('monzo_utils.model.merchant.Merchant.save')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.one')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.update')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.save')
    @patch('monzo_utils.model.merchant.Merchant.__init__')
    @patch('monzo_utils.model.merchant_address.MerchantAddress.__init__')
    def test_get_or_create_merchant_update(self, mock_merchant_address_init, mock_init_merchant, mock_merchant_address_save, mock_merchant_address_update, mock_merchant_address_one, mock_merchant_save, mock_merchant_update, mock_merchant_one, mock_init, mock_query, mock_db_init):
        mock_init.return_value = None
        mock_db_init.return_value = None
        mock_init_merchant.return_value = None
        mock_merchant_address_init.return_value = None

        merchant = Merchant()
        merchant.attributes = {
            'id': 123,
            'name': 'test'
        }

        mock_merchant_one.return_value = merchant

        merchant_addr = MerchantAddress()
        merchant_addr.attributes = {
            'id': 123,
            'name': 'test2'
        }

        mock_merchant_address_one.return_value = merchant_addr

        ms = MonzoSync()

        mo_merchant = {
            'id': 'werjoidsf',
            'name': 'test',
            'address': {
            }
        }

        merch = ms.get_or_create_merchant(mo_merchant)

        mock_merchant_one.assert_called_with('select * from merchant where merchant_id = %s', ['werjoidsf'])

        mock_init_merchant.assert_called_with()
        mock_merchant_save.assert_called_with()
        mock_merchant_update.assert_called_with({'name': 'test', 'merchant_id': 'werjoidsf'})

        self.assertEqual(merch.id, 123)

        mock_merchant_address_init.assert_called_with()
        mock_merchant_address_save.assert_called_with()
        mock_merchant_address_update.assert_called_with({'merchant_id': 123})


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    def test_sanitise(self, mock_init):
        mock_init.return_value = None

        ms = MonzoSync()

        string = 'string     with     big  spaces'

        self.assertEqual(ms.sanitise(string), 'string with big spaces')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    def test_add_transaction__with_counterparty(self, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.amount = 100

        account = Account({
            'id': 123,
            'name': 'test'
        })

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        mock_get_or_create_counterparty.assert_called_with('counterparty')


