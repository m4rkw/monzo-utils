from monzo_utils.lib.monzo_payments import MonzoPayments
from monzo_utils.model.provider import Provider
from monzo_utils.model.account import Account
from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from monzo_utils.lib.singleton import Singleton
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.model.account import Account
from monzo_utils.model.pot import Pot
from monzo_utils.model.card_payment import CardPayment
from monzo_utils.model.direct_debit import DirectDebit
from monzo_utils.model.amazon_payments import AmazonPayments
from monzo_utils.model.payment import Payment
from monzo_utils.model.finance import Finance
from monzo_utils.model.flex import Flex
from monzo_utils.model.refund import Refund
from monzo_utils.model.standing_order import StandingOrder
from freezegun import freeze_time
import os
import pwd
import json
import pytest
import datetime
import decimal

class TestMonzoPayments(BaseTest):

    def setUp(self):
        self.db = MagicMock()
        Config._instances = {}
        DB._instances[DB] = self.db

        self.config = {
            'account': 'Current'
        }

        self.homedir = pwd.getpwuid(os.getuid()).pw_dir


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.load_config')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.validate_config')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_db')
    def test_constructor(self, mock_get_db, mock_validate_config, mock_load_config):
        mock_load_config.return_value = self.config

        self.db.one.side_effect = [
            {
                "id": 1,
                "name": "Monzo"
            },
            {
                "id": 2,
                "provider_id": 1,
                "name": "Current"
            }
        ]

        mp = MonzoPayments('Current')

        self.assertEqual(mp.provider.id, 1)
        self.assertEqual(mp.provider.name, 'Monzo')
        self.assertEqual(mp.account_name, 'Current')
        self.assertEqual(mp.account.id, 2)
        self.assertEqual(mp.account.name, 'Current')
        self.assertEqual(mp.seen, [])
        self.assertEqual(mp.exchange_rates, {})

        self.assertEqual(mp.credit_tracker, f"{self.homedir}/.monzo/Current.credit")
        self.assertEqual(mp.shortfall_tracker, f"{self.homedir}/.monzo/Current.shortfall")


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.load_config')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.validate_config')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_db')
    def test_constructor_account_not_found(self, mock_get_db, mock_validate_config, mock_load_config):
        mock_load_config.return_value = self.config

        self.db.one.side_effect = [
            {
                "id": 1,
                "name": "Monzo"
            },
            None
        ]

        with pytest.raises(SystemExit) as e:
            mp = MonzoPayments('Current')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.mkdir')
    def test_load_config_nonfile_account_name_set_config_path(self, mock_mkdir, mock_exists, mock_mp):
        mock_mp.return_value = None

        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.account_name = 'Current'

        with pytest.raises(SystemExit) as e:
            mp.load_config()

        self.assertEqual(mp.config_path, f"{self.homedir}/.monzo")


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.mkdir')
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_load_config_file_account_name_set_config_path(self, mock_open, mock_yaml_load, mock_mkdir, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.return_value = True

        mp = MonzoPayments()
        mp.account_name = '/path/to/configfile.yaml'

        mp.load_config()

        self.assertEqual(mp.config_path, "/path/to")


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.mkdir')
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_load_config_file_account_name_set_account_name(self, mock_open, mock_yaml_load, mock_mkdir, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.return_value = True

        mock_yaml_load.return_value = {
            'account': 'AccountName'
        }

        mp = MonzoPayments()
        mp.account_name = '/path/to/configfile.yaml'

        mp.load_config()

        self.assertEqual(mp.account_name, 'AccountName')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.mkdir')
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_load_config_nonfile_account_name_return_config(self, mock_open, mock_yaml_load, mock_mkdir, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.side_effects = [False, True]

        mock_yaml_load.return_value = {
            'account': 'AccountName'
        }

        mp = MonzoPayments()
        mp.account_name = '/path/to/configfile.yaml'

        config = mp.load_config()

        self.assertEqual(config, {'account': 'AccountName'})


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.mkdir')
    @patch('yaml.safe_load')
    @patch('builtins.open')
    def test_load_config_file_account_name_return_config(self, mock_open, mock_yaml_load, mock_mkdir, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.return_value = True

        mock_yaml_load.return_value = {
            'account': 'AccountName'
        }

        mp = MonzoPayments()
        mp.account_name = '/path/to/configfile.yaml'

        config = mp.load_config()

        self.assertEqual(config, {'account': 'AccountName'})


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stderr.write')
    def test_validate_config_required_keys(self, mock_write, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {}

        with pytest.raises(SystemExit) as e:
            mp.validate_config()

        mock_write.assert_called_with('Missing config key: payments\n')

        mp.config = {'payments': 1}

        with pytest.raises(SystemExit) as e:
            mp.validate_config()

        mock_write.assert_called_with('Missing config key: salary_description\n')

        mp.config = {'payments': 1, 'salary_description': 1}

        with pytest.raises(SystemExit) as e:
            mp.validate_config()

        mock_write.assert_called_with('Missing config key: salary_payment_day\n')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stderr.write')
    def test_validate_config_no_notify_config_requires_no_pushover_creds(self, mock_write, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {'payments': 1, 'salary_description': 1, 'salary_payment_day': 1}

        mp.validate_config()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stderr.write')
    def test_validate_config_notify_config_requires_pushover_creds(self, mock_write, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'payments': 1,
            'salary_description': 1,
            'salary_payment_day': 1,
            'notify_shortfall': 1
        }

        with pytest.raises(SystemExit) as e:
            mp.validate_config()

        mp.config.pop('notify_shortfall')
        mp.config['notify_credit'] = 1

        with pytest.raises(SystemExit) as e:
            mp.validate_config()

        mock_write.assert_called_with('Push is enabled but push config key is missing: pushover_key\n')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_set_last_salary_date(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        last_salary_date = datetime.datetime(2024,1,1,0,0,0)
        mock_get_last_salary_date.return_value = last_salary_date

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': []
        }
        mp.json = False
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0

        mp.main()

        self.assertEqual(mp.last_salary_date, last_salary_date)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_set_next_salary_date(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        last_salary_date = datetime.datetime(2024,1,1,0,0,0)
        next_salary_date = datetime.datetime(2024,2,1,0,0,0)
        following_salary_date = datetime.datetime(2024,3,1,0,0,0)
        mock_get_last_salary_date.return_value = last_salary_date
        mock_get_next_salary_date.side_effect = [
            next_salary_date,
            following_salary_date
        ]

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': []
        }
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0
        mp.json = False

        mp.main()

        self.assertEqual(mp.next_salary_date, next_salary_date)
        self.assertEqual(mp.following_salary_date, following_salary_date)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_initialise_totals(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': []
        }
        mp.json = False
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0
        mp.next_month_bills_pot = 0

        mp.main()
        
        self.assertEqual(mp.due, 0)
        self.assertEqual(mp.total_this_month, 0)
        self.assertEqual(mp.next_month, 0)
        self.assertEqual(mp.next_month_bills_pot, 0)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_not_json_display_columns(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': []
        }
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0
        mp.json = False

        mp.main()

        mock_display_columns.assert_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_json_dont_display_columns(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': []
        }
        mp.json = True
        mp.output = ''
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0

        mp.main()

        mock_display_columns.assert_not_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_display_payment_lists(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_display_payment_list.return_value = 0, 0, 0

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': [
                {
                    'type': 'type1',
                    'payments': ['payment1']
                },
                {
                    'type': 'type2',
                    'payments': ['payment2']
                },
                {
                    'type': 'type3',
                    'payments': []
                }
            ]
        }
        mp.json = False
        mp.output = ''
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0

        mp.main()

        self.assertEqual(len(mock_display_payment_list.call_args), 2)

        mock_display_payment_list.assert_any_call({'type': 'type1', 'payments': ['payment1']}, False)
        mock_display_payment_list.assert_any_call({'type': 'type1', 'payments': ['payment1']}, True)
        mock_display_payment_list.assert_any_call({'type': 'type2', 'payments': ['payment2']}, False)
        mock_display_payment_list.assert_any_call({'type': 'type2', 'payments': ['payment2']}, True)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    def test_main_display_refunds_list(self, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_display_payment_list.return_value = 0, 0, 0

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'payments': [
                {
                    'type': 'type1',
                    'payments': ['payment1']
                },
                {
                    'type': 'type2',
                    'payments': ['payment2']
                }
            ],
            'refunds_due': ['one']
        }
        mp.json = False
        mp.output = ''
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0

        mp.main()

        mock_display_payment_list.assert_any_call({'type': 'type1', 'payments': ['payment1']}, False)
        mock_display_payment_list.assert_any_call({'type': 'type1', 'payments': ['payment1']}, True)
        mock_display_payment_list.assert_any_call({'type': 'type2', 'payments': ['payment2']}, False)
        mock_display_payment_list.assert_any_call({'type': 'type2', 'payments': ['payment2']}, True)
        mock_display_payment_list.assert_any_call({'type': 'Refund', 'payments': ['one']}, False)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.model.account.Account.get_pot')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_credit')
    def test_main_get_pot_credit(self, mock_handle_credit, mock_get_pot, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_pot = Pot()
        mock_pot.balance = 455
        mock_get_pot.return_value = mock_pot
        mock_handle_credit.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'pot': 'Test'
        }
        mp.json = False
        mp.output = ''
        mp.due = 100
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        self.assertEqual(mock_pot.balance, 455)

        mock_handle_credit.assert_called_with(mock_pot, 454.0)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.model.account.Account.get_pot')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_shortfall')
    def test_main_get_pot_shortfall(self, mock_handle_shortfall, mock_get_pot, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_pot = Pot()
        mock_pot.balance = 65
        mock_get_pot.return_value = mock_pot
        mock_handle_shortfall.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'pot': 'Test'
        }

        mp.json = False
        mp.output = ''
        mp.due = 10000
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        self.assertEqual(mock_pot.balance, 65)

        mock_handle_shortfall.assert_called_with(mock_pot, 35)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_credit')
    def test_main_no_pot_credit(self, mock_handle_credit, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_handle_credit.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
        }
        mp.json = False
        mp.output = ''
        mp.due = 500
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        mock_handle_credit.assert_called_with(mp.account, 118)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_shortfall')
    def test_main_no_pot_shortfall(self, mock_handle_shortfall, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_handle_shortfall.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":23})
        mp.config = {
        }

        mp.json = False
        mp.output = ''
        mp.due = 10000
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        mock_handle_shortfall.assert_called_with(mp.account, 77)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_shortfall')
    @patch('builtins.print')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.sanitise')
    def test_main_json_output(self, mock_sanitise, mock_print, mock_handle_shortfall, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_handle_shortfall.return_value = False
        mock_display_payment_list.return_value = 13, 130, 150
        mock_sanitise.return_value = 'sanitised output'

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":23})
        mp.config = {
            'payments': [
                {
                    'type': 'type1',
                    'payments': ['payment1']
                },
                {
                    'type': 'type2',
                    'payments': ['payment2']
                }
            ],
            'refunds_due': ['one']
        }

        mp.json = True
        mp.output = ''
        mp.due = 10000
        mp.total_this_month = 0
        mp.next_month = 0

        with freeze_time("2024-01-20"):
            mp.main()

        expected = {
            'balance': 23.0,
            'due': 100.52,
            'total_this_month': 5.2,
            'total_next_month': 6.0,
            'payments': 'sanitised output',
            'shortfall': 77.52,
            'credit': 0
        }

        print_arg = mock_print.call_args[0][0]

        try:
            data = json.loads(print_arg)
        except:
            data = None

        self.assertIsInstance(data, dict)

        self.assertIn('balance', data)
        self.assertIn('due', data)
        self.assertIn('total_this_month', data)
        self.assertIn('total_next_month', data)
        self.assertIn('payments', data)
        self.assertIn('shortfall', data)
        self.assertIn('credit', data)

        self.assertEqual(data['balance'], expected['balance'])
        self.assertEqual(data['due'], expected['due'])
        self.assertEqual(data['total_this_month'], expected['total_this_month'])
        self.assertEqual(data['total_next_month'], expected['total_next_month'])
        self.assertEqual(data['payments'], expected['payments'])
        self.assertEqual(data['shortfall'], expected['shortfall'])
        self.assertEqual(data['credit'], expected['credit'])


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.model.account.Account.get_pot')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_credit')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync')
    def test_main_sync_not_required(self, mock_sync, mock_init_sync, mock_handle_credit, mock_get_pot, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_pot = Pot()
        mock_pot.balance = 455
        mock_get_pot.return_value = mock_pot
        mock_handle_credit.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'pot': 'Test'
        }
        mp.json = False
        mp.output = ''
        mp.due = 100
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        mock_sync.assert_not_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_last_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_next_salary_date')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_columns')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.display_payment_list')
    @patch('sys.stdout.write')
    @patch('monzo_utils.model.account.Account.get_pot')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_credit')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.__init__')
    @patch('monzo_utils.lib.monzo_sync.MonzoSync.sync')
    def test_main_sync_required(self, mock_sync, mock_init_sync, mock_handle_credit, mock_get_pot, mock_stdout_write, mock_display_payment_list, mock_display_columns, mock_get_next_salary_date, mock_get_last_salary_date, mock_mp):
        mock_mp.return_value = None
        mock_pot = Pot()
        mock_pot.balance = 455
        mock_get_pot.return_value = mock_pot
        mock_handle_credit.return_value = True
        mock_init_sync.return_value = None

        mp = MonzoPayments()
        mp.shortfall_tracker = ''
        mp.account = Account()
        mp.account.update({"balance":123})
        mp.config = {
            'pot': 'Test'
        }
        mp.json = False
        mp.output = ''
        mp.due = 100
        mp.total_this_month = 100
        mp.next_month = 100

        mp.main()

        mock_sync.assert_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.flex_summary.FlexSummary.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_flex_summary_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
            'flex_account': 'Flex',
            'flex_payment_date': 19
        }
        mp.due = 0
        mp.total_this_month = 0
        mp.next_month = 0
        mp.json = False
        mp.next_month_bills_pot = 0

        mock_get_payments.return_value = [
            Flex(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Flex',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 3400)
        self.assertEqual(total_due_next_month, 3400)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.flex_summary.FlexSummary.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_flex_json_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
            'flex_account': 'Flex',
            'flex_payment_date': 19
        }
        mp.json = True
        mp.output = []
        mp.abbreviate = False
        mp.next_month_bills_pot = 0

        mock_get_payments.return_value = [
            Flex(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Flex',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 3400)
        self.assertEqual(total_due_next_month, 3400)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 2)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 34)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 2, 19))
        self.assertEqual(
            datetime.date(mp.output[0]['last_date'].year, mp.output[0]['last_date'].month, mp.output[0]['last_date'].day),
            datetime.date(2024, 1, 19)
        )
        self.assertEqual(mp.output[0]['name'], 'Flex Payment')
        self.assertEqual(mp.output[0]['payment_type'], 'Flex Summary')
        self.assertEqual(mp.output[0]['remaining'], 66)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')

        self.assertIn('amount', mp.output[1])
        self.assertIn('due_date', mp.output[1])
        self.assertIn('last_date', mp.output[1])
        self.assertIn('name', mp.output[1])
        self.assertIn('payment_type', mp.output[1])
        self.assertIn('remaining', mp.output[1])
        self.assertIn('status', mp.output[1])
        self.assertIn('suffix', mp.output[1])

        self.assertEqual(mp.output[1]['amount'], 34)
        self.assertEqual(mp.output[1]['due_date'], datetime.date(2024, 2, 19))
        self.assertEqual(
            datetime.date(mp.output[1]['last_date'].year, mp.output[1]['last_date'].month, mp.output[1]['last_date'].day),
            datetime.date(2024, 1, 19)
        )
        self.assertEqual(mp.output[1]['name'], '- thing i bought')
        self.assertEqual(mp.output[1]['payment_type'], 'Flex')
        self.assertEqual(mp.output[1]['remaining'], 66)
        self.assertEqual(mp.output[1]['status'], 'PAID')
        self.assertEqual(mp.output[1]['suffix'], '1/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.flex_summary.FlexSummary.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_flex_json_abbreviated_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
            'flex_account': 'Flex',
            'flex_payment_date': 19
        }
        mp.json = True
        mp.output = []
        mp.abbreviate = True
        mp.next_month_bills_pot = 0

        mock_get_payments.return_value = [
            Flex(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Flex',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 3400)
        self.assertEqual(total_due_next_month, 3400)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 2)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 34)
        self.assertEqual(mp.output[0]['due_date'], '19/02/24')
        self.assertEqual(mp.output[0]['last_date'], '19/01/24')
        self.assertEqual(mp.output[0]['name'], 'Flex Payment')
        self.assertEqual(mp.output[0]['payment_type'], 'FS')
        self.assertEqual(mp.output[0]['remaining'], 66)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')

        self.assertIn('amount', mp.output[1])
        self.assertIn('due_date', mp.output[1])
        self.assertIn('last_date', mp.output[1])
        self.assertIn('name', mp.output[1])
        self.assertIn('payment_type', mp.output[1])
        self.assertIn('remaining', mp.output[1])
        self.assertIn('status', mp.output[1])
        self.assertIn('suffix', mp.output[1])

        self.assertEqual(mp.output[1]['amount'], 34)
        self.assertEqual(mp.output[1]['due_date'], '19/02/24')
        self.assertEqual(mp.output[1]['last_date'], '19/01/24')
        self.assertEqual(mp.output[1]['name'], '- thing i bought')
        self.assertEqual(mp.output[1]['payment_type'], 'F')
        self.assertEqual(mp.output[1]['remaining'], 66)
        self.assertEqual(mp.output[1]['status'], 'PAID')
        self.assertEqual(mp.output[1]['suffix'], '1/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_summary_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_summary_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            True
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_json_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Card Payment')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_json_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Card Payment')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_json_abbreviated_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'CP')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.card_payment.CardPayment.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_card_payment_json_abbreviated_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            CardPayment(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'CardPayment',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'CP')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_summary_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_summary_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            True
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_json_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Direct Debit')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_json_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Direct Debit')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_json_abbreviated_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'DD')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.direct_debit.DirectDebit.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_direct_debit_json_abbreviated_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            DirectDebit(
                mp.config,
                {},
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'DirectDebit',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 100)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'DD')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_summary_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_summary_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            True
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_json_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 2, 16))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Amazon Payments')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'SKIPPED')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_json_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 2, 16))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Amazon Payments')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'SKIPPED')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_json_abbreviated_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], '16/02/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'AP')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'SKIPPED')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.amazon_payments.AmazonPayments.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_amazon_payments_json_abbreviated_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            AmazonPayments(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'AmazonPayments',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 0)
        self.assertEqual(total_due_this_month, 0)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], '16/02/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'AP')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'SKIPPED')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_summary_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_summary_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            True
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_json_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Finance')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_json_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Finance')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_json_abbreviated_monthly(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'F')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.finance.Finance.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_finance_json_abbreviated_annual(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            Finance(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Finance',
                'payments': []
            },
            True
        )

        mock_display.assert_not_called()

        self.assertEqual(due, 3333)
        self.assertEqual(total_due_this_month, 3333)
        self.assertEqual(total_due_next_month, 3333)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], 33.33)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'F')
        self.assertEqual(mp.output[0]['remaining'], 100)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '0/3')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.refund.Refund.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_refund_summary(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            Refund(
                mp.config,
                {
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                    'due_after': datetime.date(2024,1,10)
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Refund',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, -10000)
        self.assertEqual(total_due_this_month, -10000)
        self.assertEqual(total_due_next_month, 0)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.refund.Refund.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_refund_json(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = False

        mock_get_payments.return_value = [
            Refund(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                    'due_after': datetime.date(2024,1,10)
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Refund',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, -10000)
        self.assertEqual(total_due_this_month, -10000)
        self.assertEqual(total_due_next_month, 0)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], -100)
        self.assertEqual(mp.output[0]['due_date'], datetime.date(2024, 1, 10))
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'Refund')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.refund.Refund.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_refund_json_abbreviated(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.json = True
        mp.next_month_bills_pot = 0
        mp.output = []
        mp.abbreviate = True

        mock_get_payments.return_value = [
            Refund(
                mp.config,
                {
                    'payment_day': 16
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                    'due_after': datetime.date(2024,1,10)
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Refund',
                'payments': []
            },
            False
        )

        mock_display.assert_not_called()

        self.assertEqual(due, -10000)
        self.assertEqual(total_due_this_month, -10000)
        self.assertEqual(total_due_next_month, 0)

        self.assertIsInstance(mp.output, list)
        self.assertEqual(len(mp.output), 1)

        self.assertIn('amount', mp.output[0])
        self.assertIn('due_date', mp.output[0])
        self.assertIn('last_date', mp.output[0])
        self.assertIn('name', mp.output[0])
        self.assertIn('payment_type', mp.output[0])
        self.assertIn('remaining', mp.output[0])
        self.assertIn('status', mp.output[0])
        self.assertIn('suffix', mp.output[0])

        self.assertEqual(mp.output[0]['amount'], -100)
        self.assertEqual(mp.output[0]['due_date'], '10/01/24')
        self.assertEqual(mp.output[0]['last_date'], None)
        self.assertEqual(mp.output[0]['name'], 'thing i bought')
        self.assertEqual(mp.output[0]['payment_type'], 'R')
        self.assertEqual(mp.output[0]['remaining'], None)
        self.assertEqual(mp.output[0]['status'], 'DUE')
        self.assertEqual(mp.output[0]['suffix'], '')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.standing_order.StandingOrder.display')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_payments')
    @patch('sys.stdout.write')
    def test_display_payment_list_standing_order_summary(self, mock_stdout, mock_get_payments, mock_display, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)
        mp.config = {
        }
        mp.next_month_bills_pot = 0
        mp.json = False

        mock_get_payments.return_value = [
            StandingOrder(
                mp.config,
                {
                },
                {
                    'name': "thing i bought",
                    'amount': 100,
                    'start_date': datetime.date(2024,1,10),
                    'months': 3,
                    'due_after': datetime.date(2024,1,10)
                },
                mp.last_salary_date,
                mp.next_salary_date,
                mp.following_salary_date
            )
        ]

        due, total_due_this_month, total_due_next_month = mp.display_payment_list(
            {
                'type': 'Standing Order',
                'payments': []
            },
            False
        )

        mock_display.assert_called_with()

        self.assertEqual(due, 10000)
        self.assertEqual(total_due_this_month, 10000)
        self.assertEqual(total_due_next_month, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_amazon_payments_monthly(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
                'months': 3
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'months': 3,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'months': 3,
                'is_yearly': True
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Amazon Payments',
                'payments': payment_list,
                'payment_day': 1
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], AmazonPayments)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_amazon_payments_annual(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
                'months': 3
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'months': 3,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'months': 3,
                'is_yearly': True
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Amazon Payments',
                'payments': payment_list,
                'payment_day': 1
            },
            True
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        self.assertIsInstance(resp[0], AmazonPayments)
        self.assertEqual(resp[0].name, 'test payment 2')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[1], AmazonPayments)
        self.assertEqual(resp[1].name, 'test payment 3')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_card_payment_monthly(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Card Payment',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], CardPayment)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024,1,1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024,2,1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024,3,1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_card_payment_annual(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True,
                'renew_date': datetime.date(2040,1,1)
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Card Payment',
                'payments': payment_list
            },
            True
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        self.assertIsInstance(resp[0], CardPayment)
        self.assertEqual(resp[0].name, 'test payment 2')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024,1,1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024,2,1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024,3,1))

        self.assertIsInstance(resp[1], CardPayment)
        self.assertEqual(resp[1].name, 'test payment 3')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024,1,1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024,2,1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024,3,1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_direct_debit_monthly(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Direct Debit',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], DirectDebit)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_direct_debit_annual(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True,
                'renew_date': datetime.date(2040,1,1)
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Direct Debit',
                'payments': payment_list
            },
            True
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        self.assertIsInstance(resp[0], DirectDebit)
        self.assertEqual(resp[0].name, 'test payment 2')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[1], DirectDebit)
        self.assertEqual(resp[1].name, 'test payment 3')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_finance_monthly(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True,
                'renew_date': datetime.date(2040,1,1)
            }
        ]


        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Finance',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], Finance)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_finance_annual(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'amount': 123,
            },
            {
                'name': 'test payment 2',
                'amount': 234,
                'yearly_month': 4,
                'yearly_day': 4
            },
            {
                'name': 'test payment 3',
                'amount': 234,
                'is_yearly': True,
                'renew_date': datetime.date(2040,1,1)
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Finance',
                'payments': payment_list
            },
            True
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        self.assertIsInstance(resp[0], Finance)
        self.assertEqual(resp[0].name, 'test payment 2')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[1], Finance)
        self.assertEqual(resp[1].name, 'test payment 3')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_flex(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'months': 5
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key',
            'flex_payment_date': 1
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Flex',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], Flex)
        self.assertEqual(resp[0].name, '- test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_refund(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment'
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Refund',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], Refund)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_standing_order_monthly(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment'
            },
            {
                'name': 'test payment yearly',
                'yearly_month': 5,
                'yearly_day': 3
            },
            {
                'name': 'test payment yearly2',
                'is_yearly': True
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Standing Order',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        self.assertIsInstance(resp[0], StandingOrder)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_standing_order_annual(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment'
            },
            {
                'name': 'test payment yearly',
                'yearly_month': 5,
                'yearly_day': 3
            },
            {
                'name': 'test payment yearly2',
                'is_yearly': True,
                'renew_date': datetime.date(2040,1,1)
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Standing Order',
                'payments': payment_list
            },
            True
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        self.assertIsInstance(resp[0], StandingOrder)
        self.assertEqual(resp[0].name, 'test payment yearly')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[1], StandingOrder)
        self.assertEqual(resp[1].name, 'test payment yearly2')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024, 3, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_payments_sort_by_due_date(self, mock_mp):
        mock_mp.return_value = None

        payment_list = [
            {
                'name': 'test payment',
                'renew_date': datetime.date(2040,1,1)
            },
            {
                'name': 'test payment 2',
                'renew_date': datetime.date(2040,1,7)
            },
            {
                'name': 'test payment 3',
                'renew_date': datetime.date(2040,1,3)
            }
        ]

        mp = MonzoPayments()
        mp.config = {
            'config': 'key'
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.next_salary_date = datetime.date(2024,2,1)
        mp.following_salary_date = datetime.date(2024,3,1)

        resp = mp.get_payments(
            {
                'type': 'Standing Order',
                'payments': payment_list
            },
            False
        )

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 3)

        self.assertIsInstance(resp[0], StandingOrder)
        self.assertEqual(resp[0].name, 'test payment')
        self.assertEqual(resp[0].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[0].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[0].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[1], StandingOrder)
        self.assertEqual(resp[1].name, 'test payment 3')
        self.assertEqual(resp[1].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[1].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[1].following_salary_date, datetime.date(2024, 3, 1))

        self.assertIsInstance(resp[2], StandingOrder)
        self.assertEqual(resp[2].name, 'test payment 2')
        self.assertEqual(resp[2].last_salary_date, datetime.date(2024, 1, 1))
        self.assertEqual(resp[2].next_salary_date, datetime.date(2024, 2, 1))
        self.assertEqual(resp[2].following_salary_date, datetime.date(2024, 3, 1))



    @patch('pushover.Client.__init__')
    @patch('pushover.Client.send_message')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_notify(self, mock_mp, mock_send_message, mock_init):
        mock_mp.return_value = None
        mock_init.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'pushover_key': 'pushover key',
            'pushover_app': 'pushover app',
        }

        mp.notify('event', 'message')

        mock_init.assert_called_with('pushover key', api_token='pushover app')
        mock_send_message.assert_called_with('message', title='event')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_abbreviate_string(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()

        self.assertEqual('SACF', mp.abbreviate_string('String to Abbreviate Capitals From'))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.account.Account.one')
    @patch('monzo_utils.model.account.Account.last_salary_transaction')
    def test_get_last_salary_date_with_salary_account(self, mock_last_salary_transaction, mock_account_one, mock_mp):
        mock_mp.return_value = None

        account = Account({
            'id': 123,
            'name': 'test'
        })

        mock_account_one.return_value = account

        mock_last_salary_transaction.return_value = {
            'date': datetime.date(2024,1,1)
        }

        mp = MonzoPayments()
        mp.account_name = 'Joint'
        mp.provider = Provider()
        mp.provider.attributes['id'] = 7
        mp.config = {
            'salary_account': 'Current',
            'salary_description': 'SALARY',
            'salary_payment_day': 1,
            'salary_minimum': 1000
        }

        last_salary_date = mp.get_last_salary_date()

        mock_account_one.assert_called_with('select * from account where provider_id = %s and name = %s', [7, 'Current'])

        self.assertEqual(last_salary_date, datetime.date(2024, 1, 1))

        mock_last_salary_transaction.assert_called_with(description='SALARY', salary_minimum=1000, salary_payment_day=1)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.account.Account.one')
    @patch('monzo_utils.model.account.Account.last_salary_transaction')
    def test_get_last_salary_date_with_salary_account_not_found(self, mock_last_salary_transaction, mock_account_one, mock_mp):
        mock_mp.return_value = None

        account = Account({
            'id': 123,
            'name': 'test'
        })

        mock_account_one.return_value = account

        mock_last_salary_transaction.return_value = None

        mp = MonzoPayments()
        mp.account_name = 'Joint'
        mp.provider = Provider()
        mp.provider.attributes['id'] = 7
        mp.config = {
            'salary_account': 'Current',
            'salary_description': 'SALARY',
            'salary_payment_day': 1,
            'salary_minimum': 1000
        }

        with pytest.raises(SystemExit) as e:
            last_salary_date = mp.get_last_salary_date()

        mock_account_one.assert_called_with('select * from account where provider_id = %s and name = %s', [7, 'Current'])

        mock_last_salary_transaction.assert_called_with(description='SALARY', salary_minimum=1000, salary_payment_day=1)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.account.Account.__init__')
    @patch('monzo_utils.model.account.Account.last_salary_transaction')
    def test_get_last_salary_date_without_salary_account(self, mock_last_salary_transaction, mock_init_account, mock_mp):
        mock_mp.return_value = None
        mock_init_account.return_value = None

        mock_last_salary_transaction.return_value = {
            'date': datetime.date(2024,1,1)
        }

        mp = MonzoPayments()
        mp.account_name = 'Joint'
        mp.provider = Provider()
        mp.provider.attributes['id'] = 7
        mp.account = Account()
        mp.account.attributes = {'id': 3}
        mp.config = {
            'salary_description': 'SALARY',
            'salary_payment_day': 1,
            'salary_minimum': 1000
        }

        last_salary_date = mp.get_last_salary_date()

        self.assertEqual(last_salary_date, datetime.date(2024, 1, 1))

        mock_last_salary_transaction.assert_called_with(description='SALARY', salary_minimum=1000, salary_payment_day=1)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.model.account.Account.__init__')
    @patch('monzo_utils.model.account.Account.last_salary_transaction')
    def test_get_last_salary_date_without_salary_account_not_found(self, mock_last_salary_transaction, mock_init_account, mock_mp):
        mock_mp.return_value = None
        mock_init_account.return_value = None

        mock_last_salary_transaction.return_value = None

        mp = MonzoPayments()
        mp.account_name = 'Joint'
        mp.provider = Provider()
        mp.provider.attributes['id'] = 7
        mp.account = Account()
        mp.account.attributes = {'id': 3}
        mp.config = {
            'salary_description': 'SALARY',
            'salary_payment_day': 1,
            'salary_minimum': 1000
        }

        with pytest.raises(SystemExit) as e:
            last_salary_date = mp.get_last_salary_date()

        mock_last_salary_transaction.assert_called_with(description='SALARY', salary_minimum=1000, salary_payment_day=1)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 1
        }

        last_salary_date = datetime.date(2024,1,1)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2024,2,1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date_saturday(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 3
        }

        last_salary_date = datetime.date(2024,1,3)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2024,2,2))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date_sunday(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 4
        }

        last_salary_date = datetime.date(2024,1,4)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2024,2,2))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date_no_bank_holidays(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 1
        }

        last_salary_date = datetime.date(2024,3,1)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2024, 4, 1))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date_bank_holidays(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 1,
            'uk_bank_holidays': True
        }

        last_salary_date = datetime.date(2024,3,1)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2024,3,28))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_next_salary_date_bank_holidays_previous_year(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'salary_payment_day': 1,
            'uk_bank_holidays': True
        }

        last_salary_date = datetime.date(2023,12,1)
        next_salary_date = mp.get_next_salary_date(last_salary_date)

        self.assertEqual(next_salary_date, datetime.date(2023, 12, 29))


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    def test_handle_shortfall_deposit_delay(self, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_deposit_delay.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': True,
            'auto_deposit_delay_mins': 10
        }
        mp.abbreviate = False

        pot = Pot()

        mp.handle_shortfall(pot, 1001)

        mock_handle_deposit_delay.assert_called_with(1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('os.path.exists')
    def test_handle_shortfall_no_deposit_delay(self, mock_exists, mock_deposit_to_pot, mock_init_api, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_deposit_delay.return_value = False
        mock_exists.return_value = False
        mock_init_api.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': True,
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes['account_id'] = 123
        mp.shortfall_tracker = ''

        pot = Pot()

        mp.handle_shortfall(pot, 1001)

        mock_handle_deposit_delay.assert_not_called()
        mock_init_api.assert_called_with()
        mock_deposit_to_pot.assert_called_with(123, pot, 1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    def test_handle_shortfall_no_tty_notify(self, mock_notify, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_deposit_delay.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': False,
            'auto_deposit_delay_mins': 10,
            'notify_shortfall': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account"}
        mp.due = 101

        pot = Pot()
        pot.balance = 123

        mp.handle_shortfall(pot, 1001)

        mock_notify.assert_called_with('test account - shortfall', '£1001.00\n£1.01 due, £123.00 available')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('os.path.exists')
    def test_handle_shortfall_prompt_action_yes(self, mock_exists, mock_deposit_to_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_deposit_delay.return_value = False
        mock_prompt_action.return_value = True
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': False,
            'auto_deposit_delay_mins': 10,
            'prompt_deposit': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.shortfall_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_shortfall(pot, 1001)

        mock_init_api.assert_called_with()
        mock_deposit_to_pot.assert_called_with(123, pot, 1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('os.path.exists')
    def test_handle_shortfall_prompt_action_no(self, mock_exists, mock_deposit_to_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_deposit_delay.return_value = False
        mock_prompt_action.return_value = False
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': False,
            'auto_deposit_delay_mins': 10,
            'prompt_deposit': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.shortfall_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_shortfall(pot, 1001)

        mock_init_api.assert_not_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_deposit_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('os.path.exists')
    def test_handle_shortfall_notify_with_tty(self, mock_exists, mock_deposit_to_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_deposit_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_deposit_delay.return_value = False
        mock_prompt_action.return_value = False
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': False,
            'auto_deposit_delay_mins': 10,
            'notify_shortfall': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.shortfall_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_shortfall(pot, 1001)

        mock_notify.assert_called_with('test account - shortfall', '£1001.00\n£1.01 due, £123.00 available')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    def test_handle_credit_withdrawal_delay(self, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_withdrawal_delay.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_withdraw': True,
            'auto_withdraw_delay_mins': 10
        }
        mp.abbreviate = False

        pot = Pot()

        mp.handle_credit(pot, 1001)

        mock_handle_withdrawal_delay.assert_called_with(1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.withdraw_from_pot')
    @patch('os.path.exists')
    def test_handle_credit_no_withdrawal_delay(self, mock_exists, mock_withdraw_from_pot, mock_init_api, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_withdrawal_delay.return_value = False
        mock_exists.return_value = False
        mock_init_api.return_value = None

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_withdraw': True,
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes['account_id'] = 123
        mp.credit_tracker = ''

        pot = Pot()

        mp.handle_credit(pot, 1001)

        mock_handle_withdrawal_delay.assert_not_called()
        mock_init_api.assert_called_with()
        mock_withdraw_from_pot.assert_called_with(123, pot, 1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    def test_handle_credit_no_tty_notify(self, mock_notify, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = False
        mock_handle_withdrawal_delay.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_withdraw': False,
            'auto_withdrawal_delay_mins': 10,
            'notify_credit': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account"}
        mp.due = 101

        pot = Pot()
        pot.balance = 123

        mp.handle_credit(pot, 1001)

        mock_notify.assert_called_with('test account - credit', '£1001.00\n£1.01 due, £123.00 available')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.withdraw_from_pot')
    @patch('os.path.exists')
    def test_handle_credit_prompt_action_yes(self, mock_exists, mock_withdraw_from_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_withdrawal_delay.return_value = False
        mock_prompt_action.return_value = True
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_withdraw': False,
            'auto_withdrawal_delay_mins': 10,
            'prompt_withdraw': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.credit_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_credit(pot, 1001)

        mock_init_api.assert_called_with()
        mock_withdraw_from_pot.assert_called_with(123, pot, 1001)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('os.path.exists')
    def test_handle_credit_prompt_action_no(self, mock_exists, mock_deposit_to_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_withdrawal_delay.return_value = False
        mock_prompt_action.return_value = False
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_deposit': False,
            'auto_withdrawal_delay_mins': 10,
            'prompt_deposit': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.shortfall_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_credit(pot, 1001)

        mock_init_api.assert_not_called()


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.handle_withdrawal_delay')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.notify')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.prompt_action')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.withdraw_from_pot')
    @patch('os.path.exists')
    def test_handle_credit_notify_with_tty(self, mock_exists, mock_withdraw_from_pot, mock_init_api, mock_prompt_action, mock_notify, mock_handle_withdrawal_delay, mock_tty, mock_mp):
        mock_mp.return_value = None
        mock_tty.return_value = True
        mock_handle_withdrawal_delay.return_value = False
        mock_prompt_action.return_value = False
        mock_init_api.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.config = {
            'pot': 'Bills',
            'auto_withdraw': False,
            'auto_withdrawal_delay_mins': 10,
            'notify_credit': True
        }
        mp.abbreviate = False
        mp.account = Account()
        mp.account.attributes = {'name': "test account",'account_id':123}
        mp.due = 101
        mp.shortfall_tracker = ''

        pot = Pot()
        pot.balance = 123

        mp.handle_credit(pot, 1001)

        mock_notify.assert_called_with('test account - credit', '£1001.00\n£1.01 due, £123.00 available')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_handle_withdrawal_delay_create_file(self, mock_open, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.credit_tracker = '/tmp/credit'

        resp = mp.handle_withdrawal_delay(1001)

        self.assertEqual(resp, False)

        mock_open.assert_called_with('/tmp/credit', 'w')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_file_contents')
    @patch('time.time')
    def test_handle_withdrawal_delay_elapsed(self, mock_time, mock_get_file_contents, mock_stat, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_get_file_contents.return_value = '100100'

        stat = MagicMock()
        stat.st_mtime = 100100000

        mock_time.return_value = 100100000 + 599

        mock_stat.return_value = stat

        mp = MonzoPayments()
        mp.credit_tracker = '/tmp/credit'
        mp.config = {
            'auto_withdraw_delay_mins': 10
        }

        for i in range(0, 1200):
            mock_time.return_value = 100100000 + i

            resp = mp.handle_withdrawal_delay(1001)

            if i >= 600:
                self.assertEqual(resp, True)
            else:
                self.assertEqual(resp, False)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_handle_deposit_delay_create_file(self, mock_open, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_exists.return_value = False

        mp = MonzoPayments()
        mp.shortfall_tracker = '/tmp/credit'

        resp = mp.handle_deposit_delay(1001)

        self.assertEqual(resp, False)

        mock_open.assert_called_with('/tmp/credit', 'w')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.get_file_contents')
    @patch('time.time')
    def test_handle_deposit_delay_elapsed(self, mock_time, mock_get_file_contents, mock_stat, mock_exists, mock_mp):
        mock_mp.return_value = None
        mock_get_file_contents.return_value = '100100'

        stat = MagicMock()
        stat.st_mtime = 100100000

        mock_time.return_value = 100100000 + 599

        mock_stat.return_value = stat

        mp = MonzoPayments()
        mp.shortfall_tracker = '/tmp/credit'
        mp.config = {
            'auto_deposit_delay_mins': 10
        }

        for i in range(0, 1200):
            mock_time.return_value = 100100000 + i

            resp = mp.handle_deposit_delay(1001)

            if i >= 600:
                self.assertEqual(resp, True)
            else:
                self.assertEqual(resp, False)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_sanitise_date(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()

        data = [
            {
                'key1': datetime.date(2024,1,1)
            }
        ]

        output = mp.sanitise(data)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 1)
        self.assertIn('key1', output[0])
        self.assertEqual(output[0]['key1'], '2024-01-01')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_sanitise_datetime(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()

        data = [
            {
                'key1': datetime.datetime(2024,1,1,13,44,11)
            }
        ]

        output = mp.sanitise(data)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 1)
        self.assertIn('key1', output[0])
        self.assertEqual(output[0]['key1'], '2024-01-01 13:44:11')


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_sanitise_decimal(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()

        data = [
            {
                'key1': decimal.Decimal(204.11)
            }
        ]

        output = mp.sanitise(data)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 1)
        self.assertIn('key1', output[0])
        self.assertIsInstance(output[0]['key1'], float)
        self.assertEqual(output[0]['key1'], 204.11)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_sanitise_default(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()

        data = [
            {
                'key1': '123'
            },
            {
                'key2': 456
            },
            {
                'key3': 15554.44
            }
        ]

        output = mp.sanitise(data)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 3)
        self.assertIn('key1', output[0])
        self.assertIn('key2', output[1])
        self.assertIn('key3', output[2])
        self.assertIsInstance(output[0]['key1'], str)
        self.assertIsInstance(output[1]['key2'], int)
        self.assertIsInstance(output[2]['key3'], float)
        self.assertEqual(output[0]['key1'], '123')
        self.assertEqual(output[1]['key2'], 456)
        self.assertEqual(output[2]['key3'], 15554.44)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_check_pot_payments_no_config(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {}

        resp = mp.check_pot_payments()

        self.assertEqual(resp, False)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.deposit_to_pot')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.model.pot.Pot.one')
    def test_check_pot_payments_no_config(self, mock_pot_one, mock_init, mock_deposit_to_pot, mock_mp):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_init.return_value = None
        mock_mp.return_value = None

        pot = Pot({
            'id': 123,
            'name': 'test',
            'last_monthly_transfer_date': datetime.date(2024,1,2)
        })

        mock_pot_one.return_value = pot

        mp = MonzoPayments()
        mp.config = {
            'payments_to_pots': [
                {
                    'name': 'Test',
                    'amount': 123
                }
            ]
        }
        mp.last_salary_date = datetime.date(2024,1,1)
        mp.account = Account()
        mp.account.attributes = {'account_id': 456}

        resp = mp.check_pot_payments()

        self.assertEqual(resp, True)

        args = mock_deposit_to_pot.call_args[0]

        self.assertEqual(args[0], 456)
        self.assertIsInstance(args[1], Pot)
        self.assertEqual(args[2], 123)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_transfer_amount_fixed(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {}

        pot = Pot()

        payment = {
            'amount': 100
        }

        resp = mp.get_transfer_amount(pot, payment)

        self.assertEqual(resp, 10000)


    @patch('monzo_utils.lib.monzo_payments.MonzoPayments.__init__')
    def test_get_transfer_amount_topup(self, mock_mp):
        mock_mp.return_value = None

        mp = MonzoPayments()
        mp.config = {}

        pot = Pot()
        pot.attributes['balance'] = 50

        payment = {
            'amount': 100,
            'topup': True
        }

        resp = mp.get_transfer_amount(pot, payment)

        self.assertEqual(resp, 5000)


