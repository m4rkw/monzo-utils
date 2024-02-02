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
from monzo_utils.model.transaction import Transaction
from monzo_utils.model.counterparty import Counterparty
from monzo_utils.model.provider import Provider
from monzo_utils.model.pot import Pot
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
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_provider')
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
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_provider')
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


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__same_as_description(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.amount = 100

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc'
        })

        mock_get_or_create_counterparty.return_value = counterparty

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertIn('description', args)
        self.assertEqual(args['description'], 'counterparty desc')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__different_from_description(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.amount = 100

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        mock_get_or_create_counterparty.return_value = counterparty

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertIn('description', args)
        self.assertEqual(args['description'], 'counterparty desc 123 counterparty desc')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__credit__no_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = 1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'credit')
        self.assertEqual(args['description'], 'counterparty desc 123 counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], 12)
        self.assertEqual(args['money_out'], None)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], 123)
        self.assertEqual(args['pot_id'], None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__credit__with_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = 1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'credit')
        self.assertEqual(args['description'], 'counterparty desc 123 counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], 12)
        self.assertEqual(args['money_out'], None)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], 123)
        self.assertEqual(args['pot_id'], 707)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__debit__no_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'debit')
        self.assertEqual(args['description'], 'counterparty desc 123 counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], None)
        self.assertEqual(args['money_out'], 12)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], 123)
        self.assertEqual(args['pot_id'], None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__debit__with_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'debit')
        self.assertEqual(args['description'], 'counterparty desc 123 counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], None)
        self.assertEqual(args['money_out'], 12)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], 123)
        self.assertEqual(args['pot_id'], 707)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.db.DB.create')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__with_counterparty__metadata(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_create, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = 'counterparty'
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''
        mo_t.atm_fees_detailed = {
            'one': 'two',
            'three': 'four'
        }
        mo_t.categories = {
            'shopping': 'test',
            'blah': 'test2'
        }
        mo_t.fees = {
            'three': 'four',
            'blah': 'foo'
        }
        mo_t.metadata = {
            'bloop': 'bleep'
        }

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'atm_fees_detailed_three', 'value': 'four'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'categories_blah', 'value': 'test2'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'fees_blah', 'value': 'foo'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'metadata_bloop', 'value': 'bleep'})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    def test_add_transaction__without_counterparty(self, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.amount = 100
        mo_t.description = 'test'

        account = Account({
            'id': 123,
            'name': 'test'
        })

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        mock_get_or_create_counterparty.assert_not_called()


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty_sanitise_description(self, mock_transaction_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.amount = 100
        mo_t.description = 'test  dfsd    sdfsd3          fwef'

        tr = Transaction({
            'id': 123
        })

        mock_transaction_one.return_value = tr

        account = Account({
            'id': 123,
            'name': 'test'
        })

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_transaction_update.call_args[0][0]

        self.assertIn('description', args)
        self.assertEqual(args['description'], 'test dfsd sdfsd3 fwef')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__same_as_description(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.amount = 100

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc'
        })

        mock_get_or_create_counterparty.return_value = counterparty

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertIn('description', args)
        self.assertEqual(args['description'], 'counterparty desc')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__different_from_description(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.amount = 100

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        mock_get_or_create_counterparty.return_value = counterparty

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertIn('description', args)
        self.assertEqual(args['description'], 'counterparty desc')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__credit__no_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = 1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'credit')
        self.assertEqual(args['description'], 'counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], 12)
        self.assertEqual(args['money_out'], None)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], None)
        self.assertEqual(args['pot_id'], None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__credit__with_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = 1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'credit')
        self.assertEqual(args['description'], 'counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], 12)
        self.assertEqual(args['money_out'], None)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], None)
        self.assertEqual(args['pot_id'], 707)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__debit__no_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3])

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'debit')
        self.assertEqual(args['description'], 'counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], None)
        self.assertEqual(args['money_out'], 12)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], None)
        self.assertEqual(args['pot_id'], None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__debit__with_pot(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        args = mock_update.call_args[0][0]

        self.assertIsInstance(args, dict)
        self.assertEqual(args['account_id'], 123)
        self.assertEqual(args['transaction_id'], 12)
        self.assertEqual(args['date'], '2024-01-01')
        self.assertEqual(args['type'], 'debit')
        self.assertEqual(args['description'], 'counterparty desc')
        self.assertEqual(args['ref'], 'counterparty desc')
        self.assertEqual(args['money_in'], None)
        self.assertEqual(args['money_out'], 12)
        self.assertEqual(args['pending'], False)
        self.assertEqual(args['created_at'], datetime.date(2024,1,1))
        self.assertEqual(args['updated_at'], datetime.date(2024,2,1))
        self.assertEqual(args['currency'], 'GBP')
        self.assertEqual(args['local_currency'], 'GBP')
        self.assertEqual(args['local_amount'], 1200)
        self.assertEqual(args['merchant_id'], 456)
        self.assertEqual(args['notes'], 'notes')
        self.assertEqual(args['originator'], 'originator')
        self.assertEqual(args['scheme'], 'scheme')
        self.assertEqual(args['settled'], True)
        self.assertEqual(args['declined'], 0)
        self.assertEqual(args['decline_reason'], '')
        self.assertEqual(args['counterparty_id'], None)
        self.assertEqual(args['pot_id'], 707)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.lib.db.DB.create')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_counterparty')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_merchant')
    @patch('monzo_utils.model.transaction.Transaction.save')
    @patch('monzo_utils.model.transaction.Transaction.one')
    @patch('monzo_utils.model.transaction.Transaction.update')
    def test_add_transaction__without_counterparty__metadata(self, mock_update, mock_transaction_one, mock_save_transaction, mock_get_or_create_merchant, mock_get_or_create_counterparty, mock_init, mock_create, mock_db_query, mock_db_init):
        mock_db_init.return_value = None
        mock_init.return_value = None

        mo_t = MagicMock()
        mo_t.counterparty = None
        mo_t.description = 'counterparty desc'
        mo_t.transaction_id = 12
        mo_t.amount = -1200
        mo_t.created = datetime.date(2024,1,1)
        mo_t.updated = datetime.date(2024,2,1)
        mo_t.amount_is_pending = False
        mo_t.currency = 'GBP'
        mo_t.local_currency = 'GBP'
        mo_t.local_amount = 1200
        mo_t.notes = 'notes'
        mo_t.originator = 'originator'
        mo_t.scheme = 'scheme'
        mo_t.settled = True
        mo_t.decline_reason = ''
        mo_t.atm_fees_detailed = {
            'one': 'two',
            'three': 'four'
        }
        mo_t.categories = {
            'shopping': 'test',
            'blah': 'test2'
        }
        mo_t.fees = {
            'three': 'four',
            'blah': 'foo'
        }
        mo_t.metadata = {
            'bloop': 'bleep'
        }

        account = Account({
            'id': 123,
            'name': 'test'
        })

        transaction = Transaction({
            'id': 123,
            'money_out': 100,
            'description': 'counterparty'
        })

        counterparty = Counterparty({
            'id': 123,
            'name': 'counterparty desc 123'
        })

        merchant = Merchant({
            'id': 456,
            'name': 'test'
        })

        mock_get_or_create_counterparty.return_value = counterparty
        mock_get_or_create_merchant.return_value = merchant

        mock_transaction_one.return_value = transaction

        ms = MonzoSync()
        ms.add_transaction(account, mo_t, [1,2,3], 707)

        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'atm_fees_detailed_three', 'value': 'four'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'categories_blah', 'value': 'test2'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'fees_blah', 'value': 'foo'})
        mock_create.assert_any_call('transaction_metadata', {'transaction_id': 123, 'key': 'metadata_bloop', 'value': 'bleep'})


    @patch('monzo_utils.model.counterparty.Counterparty.one')
    @patch('monzo_utils.model.counterparty.Counterparty.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.counterparty.Counterparty.update')
    @patch('monzo_utils.model.counterparty.Counterparty.save')
    def test_get_or_create_counterparty__create(self, mock_save, mock_update, mock_init, mock_cp_init, mock_one):
        mock_init.return_value = None
        mock_cp_init.return_value = None
        mock_one.return_value = None

        mo_t = MagicMock()

        ms = MonzoSync()

        created_cp = ms.get_or_create_counterparty(mo_t)

        self.assertEqual(created_cp.id, None)

        mock_init.assert_called_with()

        mock_update.assert_called_with(mo_t)


    @patch('monzo_utils.model.counterparty.Counterparty.one')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.counterparty.Counterparty.update')
    @patch('monzo_utils.model.counterparty.Counterparty.save')
    def test_get_or_create_counterparty__update(self, mock_save, mock_update, mock_init, mock_one):
        mock_init.return_value = None

        cp = Counterparty({
            'id': 123,
            'name': 'test'
        })
        mock_one.return_value = cp

        mo_t = MagicMock()

        ms = MonzoSync()

        updated_cp = ms.get_or_create_counterparty(mo_t)

        self.assertEqual(updated_cp.id, 123)


    @patch('monzo_utils.model.provider.Provider.one')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.provider.Provider.save')
    def test_get_or_create_provider__create(self, mock_save, mock_init, mock_one):
        mock_init.return_value = None
        mock_one.return_value = None

        ms = MonzoSync()

        created = ms.get_or_create_provider('provider name')

        self.assertEqual(created.id, None)

        mock_init.assert_called_with()
        mock_save.assert_called_with()


    @patch('monzo_utils.model.provider.Provider.one')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.provider.Provider.save')
    def test_get_or_create_provider__create(self, mock_save, mock_init, mock_one):
        mock_init.return_value = None

        ms = MonzoSync()

        provider = Provider({
            'id': 123,
            'name': 'test'
        })

        mock_one.return_value = provider

        updated = ms.get_or_create_provider('provider name')

        self.assertEqual(updated.id, 123)

        mock_save.assert_not_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.accounts')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync_account')
    @patch('pathlib.Path.touch')
    def test_sync__ignore_monzoflexbackingloan(self, mock_touch, mock_sync_account, mock_init, mock_accounts, mock_api_init):
        mock_init.return_value = None
        mock_api_init.return_value = None

        account1 = MagicMock()
        account1.account_id = 123
        account1.description = 'desc1'

        account2 = MagicMock()
        account2.account_id = 234
        account2.description = 'desc2'

        account3 = MagicMock()
        account3.account_id = 345
        account3.description = 'monzoflexbackingloan_3943'

        mock_accounts.return_value = [
            account1,
            account2,
            account3
        ]

        Config().accounts = [123, 234, 345]

        api = MonzoAPI()

        ms = MonzoSync()
        ms.api = api
        ms.sync()

        args = mock_sync_account.call_args

        self.assertEqual(mock_sync_account.call_count, 2)

        mock_sync_account.assert_any_call(account1, 3)
        mock_sync_account.assert_any_call(account2, 3)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.accounts')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync_account')
    @patch('pathlib.Path.touch')
    def test_sync__ignore_not_in_list(self, mock_touch, mock_sync_account, mock_init, mock_accounts, mock_api_init):
        mock_init.return_value = None
        mock_api_init.return_value = None

        account1 = MagicMock()
        account1.account_id = 123
        account1.description = 'desc1'

        account2 = MagicMock()
        account2.account_id = 234
        account2.description = 'desc2'

        account3 = MagicMock()
        account3.account_id = 345
        account3.description = 'desc3'

        mock_accounts.return_value = [
            account1,
            account2,
            account3
        ]

        Config().accounts = [123, 345]

        api = MonzoAPI()

        ms = MonzoSync()
        ms.api = api
        ms.sync()

        args = mock_sync_account.call_args

        self.assertEqual(mock_sync_account.call_count, 2)

        mock_sync_account.assert_any_call(account1, 3)
        mock_sync_account.assert_any_call(account3, 3)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.get_or_create_account')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync_account_pots')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync_account_transactions')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync_account_pot_transactions')
    def test_sync_account(self, mock_sync_account_pot_transactions, mock_sync_account_transactions, mock_sync_account_pots, mock_get_or_create_account, mock_init):
        mock_init.return_value = None

        account = Account({
            'id': 123,
            'name': 'test'
        })

        mock_get_or_create_account.return_value = account
        mock_sync_account_pots.return_value = {
            10: 'test'
        }
        mock_sync_account_transactions.return_value = [12,1], 2

        mo_account = MagicMock()
        mo_account.account_id = 123

        Config().accounts = {
            123: {
                'name': 'test'
            }
        }

        ms = MonzoSync()
        ms.sync_account(mo_account, 7)

        mock_get_or_create_account.assert_called_with(mo_account, {'name': 'test'})
        mock_sync_account_pots.assert_called_with(account)
        mock_sync_account_transactions.assert_called_with(account, {10:'test'}, 7)
        mock_sync_account_pot_transactions.assert_called_with(account, [12,1], {10:'test'}, 2, 7)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.add_transaction')
    @patch('os.system')
    def test_sync_account_transactions(self, mock_system, mock_add_transaction, mock_init):
        mo_transactions = [
            'one',
            'two',
            'three'
        ]

        mock_init.return_value = None

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.transactions.return_value = mo_transactions

        account = MagicMock()
        account.account_id = 123

        pot_lookup = {}

        pot_account_ids, total = ms.sync_account_transactions(account, pot_lookup, 7)

        mock_add_transaction.assert_any_call(account, 'one', {})
        mock_add_transaction.assert_any_call(account, 'two', {})
        mock_add_transaction.assert_any_call(account, 'three', {})

        self.assertEqual(pot_account_ids, {})
        self.assertEqual(total, 3)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.add_transaction')
    @patch('os.system')
    def test_sync_account_pot_transactions(self, mock_system, mock_add_transaction, mock_init):
        mo_transactions = [
            'one',
            'two',
            'three'
        ]

        mock_init.return_value = None

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.transactions.return_value = mo_transactions

        account = MagicMock()
        account.account_id = 123

        pot_account_ids = {
            123: 456
        }

        pot = MagicMock()
        pot.deleted = False
        pot.id = 789

        pot_lookup = {
            456: pot
        }

        ms.sync_account_pot_transactions(account, pot_account_ids, pot_lookup, 2, 7)

        self.assertEqual(mock_add_transaction.call_count, 3)

        mock_add_transaction.assert_any_call(account, 'one', pot_account_ids, 789)
        mock_add_transaction.assert_any_call(account, 'two', pot_account_ids, 789)
        mock_add_transaction.assert_any_call(account, 'three', pot_account_ids, 789)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.add_transaction')
    @patch('os.system')
    def test_sync_account_pot_transactions_skip_deleted(self, mock_system, mock_add_transaction, mock_init):
        mo_transactions = [
            'one',
            'two',
            'three'
        ]

        mock_init.return_value = None

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.transactions.return_value = mo_transactions

        account = MagicMock()
        account.account_id = 123

        pot_account_ids = {
            123: 456,
            234: 994
        }

        pot = MagicMock()
        pot.deleted = False
        pot.id = 789

        pot2 = MagicMock()
        pot2.deleted = True
        pot2.id = 999

        pot_lookup = {
            456: pot,
            994: pot2
        }

        ms.sync_account_pot_transactions(account, pot_account_ids, pot_lookup, 2, 7)

        self.assertEqual(mock_add_transaction.call_count, 3)

        mock_add_transaction.assert_any_call(account, 'one', pot_account_ids, 789)
        mock_add_transaction.assert_any_call(account, 'two', pot_account_ids, 789)
        mock_add_transaction.assert_any_call(account, 'three', pot_account_ids, 789)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.pot.Pot.save')
    @patch('monzo_utils.model.pot.Pot.one')
    def test_sync_account_pots_create(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None

        pot1 = MagicMock()
        pot1.pot_id = 234
        pot2 = MagicMock()
        pot2.pot_id = 456

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.pots.return_value = [pot1, pot2]

        account = MagicMock()
        account.account_id = 123

        mock_one.return_value = None

        pot_lookup = ms.sync_account_pots(account)

        self.assertIsInstance(pot_lookup, dict)
        self.assertIn(234, pot_lookup)
        self.assertIn(456, pot_lookup)

        self.assertIsInstance(pot_lookup[234], Pot)
        self.assertIsInstance(pot_lookup[456], Pot)

        self.assertEqual(pot_lookup[234].id, None)
        self.assertEqual(pot_lookup[456].id, None)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.pot.Pot.save')
    @patch('monzo_utils.model.pot.Pot.one')
    def test_sync_account_pots_update(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None

        pot1 = MagicMock()
        pot1.pot_id = 234
        pot2 = MagicMock()
        pot2.pot_id = 456

        ms = MonzoSync()
        ms.api = MagicMock()
        ms.api.pots.return_value = [pot1, pot2]

        account = MagicMock()
        account.account_id = 123

        pot1 = Pot({
            'id': 22
        })
        pot2 = Pot({
            'id': 88
        })

        mock_one.side_effect = [pot1, pot2]

        pot_lookup = ms.sync_account_pots(account)

        self.assertIsInstance(pot_lookup, dict)
        self.assertIn(234, pot_lookup)
        self.assertIn(456, pot_lookup)

        self.assertIsInstance(pot_lookup[234], Pot)
        self.assertIsInstance(pot_lookup[456], Pot)

        self.assertEqual(pot_lookup[234].id, 22)
        self.assertEqual(pot_lookup[456].id, 88)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.account.Account.save')
    @patch('monzo_utils.model.account.Account.one')
    def test_get_or_create_account__bank__create(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None
        mock_one.return_value = None

        ms = MonzoSync()
        ms.provider = Provider({
            'id': 123,
            'name': 'provider'
        })

        mo_account = MagicMock()
        mo_account.account_id = 54545
        mo_account.balance.balance = 1230

        account_config = {
            'sortcode': '01-01-01',
            'account_no': '10101010',
            'name': 'test'
        }

        account = ms.get_or_create_account(mo_account, account_config)

        self.assertIsInstance(account, Account)
        self.assertEqual(account.id, None)
        self.assertEqual(account.provider_id, 123)
        self.assertEqual(account.name, 'test')
        self.assertEqual(account.account_id, 54545)
        self.assertEqual(account.type, 'bank')
        self.assertEqual(account.balance, 12.3)
        self.assertEqual(account.sortcode, '01-01-01')
        self.assertEqual(account.account_no, '10101010')


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.account.Account.save')
    @patch('monzo_utils.model.account.Account.one')
    def test_get_or_create_account__bank__update(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None

        account = Account({
            'id': 9292,
            'name': 'test'
        })

        mock_one.return_value = account

        ms = MonzoSync()
        ms.provider = Provider({
            'id': 123,
            'name': 'provider'
        })

        mo_account = MagicMock()
        mo_account.account_id = 54545
        mo_account.balance.balance = 1230

        account_config = {
            'sortcode': '01-01-01',
            'account_no': '10101010',
            'name': 'test'
        }

        account = ms.get_or_create_account(mo_account, account_config)

        self.assertIsInstance(account, Account)
        self.assertEqual(account.id, 9292)
        self.assertEqual(account.provider_id, 123)
        self.assertEqual(account.name, 'test')
        self.assertEqual(account.account_id, 54545)
        self.assertEqual(account.type, 'bank')
        self.assertEqual(account.balance, 12.3)
        self.assertEqual(account.sortcode, '01-01-01')
        self.assertEqual(account.account_no, '10101010')


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.account.Account.save')
    @patch('monzo_utils.model.account.Account.one')
    def test_get_or_create_account__credit__create(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None
        mock_one.return_value = None

        ms = MonzoSync()
        ms.provider = Provider({
            'id': 123,
            'name': 'provider'
        })

        mo_account = MagicMock()
        mo_account.account_id = 54545
        mo_account.balance.balance = -1230

        account_config = {
            'name': 'test',
            'credit_limit': 1000
        }

        account = ms.get_or_create_account(mo_account, account_config)

        self.assertIsInstance(account, Account)
        self.assertEqual(account.id, None)
        self.assertEqual(account.provider_id, 123)
        self.assertEqual(account.name, 'test')
        self.assertEqual(account.account_id, 54545)
        self.assertEqual(account.type, 'credit')
        self.assertEqual(account.balance, 12.3)
        self.assertEqual(account.available, 987.7)


    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.model.account.Account.save')
    @patch('monzo_utils.model.account.Account.one')
    def test_get_or_create_account__credit__update(self, mock_one, mock_save, mock_init):
        mock_init.return_value = None

        account = Account({
            'id': 9292,
            'name': 'test'
        })

        mock_one.return_value = account

        ms = MonzoSync()
        ms.provider = Provider({
            'id': 123,
            'name': 'provider'
        })

        mo_account = MagicMock()
        mo_account.account_id = 54545
        mo_account.balance.balance = -8778

        account_config = {
            'name': 'test',
            'credit_limit': 1000
        }

        account = ms.get_or_create_account(mo_account, account_config)

        self.assertIsInstance(account, Account)
        self.assertEqual(account.id, 9292)
        self.assertEqual(account.provider_id, 123)
        self.assertEqual(account.name, 'test')
        self.assertEqual(account.account_id, 54545)
        self.assertEqual(account.type, 'credit')
        self.assertEqual(account.balance, 87.78)
        self.assertEqual(account.available, 912.22)
