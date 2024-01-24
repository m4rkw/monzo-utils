from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from monzo_utils.model.finance import Finance
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.lib.transactions_seen import TransactionsSeen
import pytest
import datetime
import decimal
import json
from freezegun import freeze_time

class TestFinance(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}
        TransactionsSeen().seen = {}


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_constructor(self, mock_query, mock_init):
        with freeze_time("2024-01-01"):
            p = Finance(
                'config',
                'payment_list_config',
                'payment_config',
                'last_salary_date',
                'next_salary_date',
                'following_salary_date'
            )

            self.assertEqual(p.config, 'config')
            self.assertEqual(p.payment_list_config, 'payment_list_config')
            self.assertEqual(p.payment_config, 'payment_config')
            self.assertEqual(p.last_salary_date, 'last_salary_date')
            self.assertEqual(p.next_salary_date, 'next_salary_date')
            self.assertEqual(p.following_salary_date, 'following_salary_date')

            self.assertEqual(p.today, datetime.datetime(2024,1,1))
            self.assertEqual(p.cache, {})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_data_fields(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            'config',
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,1,1),
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
        )
        p.cache['last_date'] = datetime.date(2024,1,1)

        data = p.data()

        self.assertIn('amount', data)
        self.assertIn('due_date', data)
        self.assertIn('last_date', data)
        self.assertIn('name', data)
        self.assertIn('payment_type', data)
        self.assertIn('remaining', data)
        self.assertIn('status', data)
        self.assertIn('suffix', data)

        self.assertEqual(data['amount'], 24.6)
        self.assertEqual(data['due_date'], datetime.date(2024, 2, 1))
        self.assertEqual(data['last_date'], datetime.date(2024, 1, 1))
        self.assertEqual(data['name'], 'payment')
        self.assertEqual(data['payment_type'], 'Finance')
        self.assertEqual(data['remaining'], 123)
        self.assertEqual(data['status'], 'PAID')
        self.assertEqual(data['suffix'], '0/5')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_data_abbreviated(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            'config',
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,1,1),
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
        )
        p.cache['last_date'] = datetime.date(2024,1,1)

        data = p.data(True)

        self.assertIn('amount', data)
        self.assertIn('due_date', data)
        self.assertIn('last_date', data)
        self.assertIn('name', data)
        self.assertIn('payment_type', data)
        self.assertIn('remaining', data)
        self.assertIn('status', data)
        self.assertIn('suffix', data)

        self.assertEqual(data['amount'], 24.6)
        self.assertEqual(data['due_date'], '01/02/24')
        self.assertEqual(data['last_date'], '01/01/24')
        self.assertEqual(data['name'], 'payment')
        self.assertEqual(data['payment_type'], 'F')
        self.assertEqual(data['remaining'], 123)
        self.assertEqual(data['status'], 'PAID')
        self.assertEqual(data['suffix'], '0/5')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_abbreviate(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            'config',
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,1,1),
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
        )

        self.assertEqual(p.abbreviate('Test One Two Three'), 'TOTT')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_short_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            'config',
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,1,1),
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
        )

        self.assertEqual(p.short_date(None), None)
        self.assertEqual(p.short_date(datetime.date(2024,1,1)), '01/01/24')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('builtins.print')
    def test_display(self, mock_print, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            'config',
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,1,1),
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
        )

        p.display()

        mock_print.assert_called_with('    DUE: Finance         payment                   0/5   £24.60              £123.00               ')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('builtins.print')
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    def test_display_last_amount_override(self, mock_last_payment, mock_print, mock_query, mock_db):
        mock_db.return_value = None

        last_payment = Transaction({
            'id': 123,
            'date': datetime.date(2024,1,1),
            'money_out': 1234
        })

        mock_last_payment.return_value = last_payment

        with freeze_time('2024-01-22'):
            p = Finance(
                {
                    'last_amount_overrides': {
                        'payment': {
                            datetime.date(2024,1,1): 2020
                        }
                    }
                },
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,1,1),
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
            )

            p.cache['last_payment'] = Transaction()
            p.cache['last_payment'].id = 123
            p.cache['last_payment'].money_out = 123

            p.display()

            mock_print.assert_called_with('   PAID: Finance         payment                   0/5   £2020.00            £123.00  2024-01-01   2024-02-01')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_name(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                'config',
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,1,1),
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
            )

            self.assertEqual(p.name, 'payment')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_status_due(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,1,1),
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
            )

            self.assertEqual(p.status, 'DUE')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_status_skip_next_month(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'start_date': datetime.date(2024,3,1),
                    'months': 5
                },
                datetime.date(2024,1,1),
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
            )

            self.assertEqual(p.status, 'SKIPPED')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.yearly_payment_due_this_month')
    def test_status_yearly_month(self, mock_due_this_month, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'yearly_month': 2,
                    'yearly_day': 1,
                    'months': 5
                },
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            mock_due_this_month.return_value = False

            self.assertEqual(p.status, 'SKIPPED')

            mock_due_this_month.return_value = True

            self.assertEqual(p.status, 'DUE')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_status_renew_date(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            p.payment_config['renew_date'] = datetime.date(2024,3,1)

            self.assertEqual(p.status, 'SKIPPED')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_status_exclude_months(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            p.payment_config['exclude_months'] = [1]

            self.assertEqual(p.status, 'SKIPPED')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_date', new_callable=PropertyMock)
    def test_status_last_date(self, mock_last_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_last_date.return_value = datetime.date(2024,1,1)

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            mock_last_date.return_value = datetime.date(2024,2,1)

            self.assertEqual(p.status, 'PAID')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.due_date', new_callable=PropertyMock)
    def test_status_due_date(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = datetime.date(2024,1,1)

        with freeze_time('2024-01-22'):
            p = Finance(
                {},
                'payment_list_config',
                {
                    'name': 'payment',
                    'amount': 123,
                    'months': 5
                },
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            mock_due_date.return_value = datetime.date(2024,3,1)

            self.assertEqual(p.status, 'SKIPPED')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_payment_type(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.payment_type, 'Finance')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_num_paid(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.num_paid, 0)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_num_total(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.num_total, 5)

        p.payment_config['months'] = 3

        self.assertEqual(p.num_total, 3)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_remaining(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.remaining, 123)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_override_dont_override(self, mock_query, mock_db):
        mock_db.return_value = None

        config = Config({
            'last_amount_overrides': {
                'payment': {
                    datetime.date(2024,2,1): 456
                }
            }
        })

        Config._instances = {Config: config}

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_renewal_first_payment_ignore(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,1,15),
                    'amount': 456,
                    'first_payment': 789
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-15"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_renewal_first_payment_before_renewal_ignore(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,1,15),
                    'amount': 456,
                    'first_payment': 789
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-14"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_renewal_regular_payment_ignore(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,1,15),
                    'amount': 456,
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-15"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_date', new_callable=PropertyMock)
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    def test_display_amount_renewal_last_payment_ignore(self, mock_last_payment, mock_last_date, mock_query, mock_db):
        mock_db.return_value = None
        last_payment = Transaction({"money_out": 234})
        mock_last_payment.return_value = last_payment
        mock_last_date.return_value = datetime.date(2024,1,16)

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,1,15),
                    'amount': 456,
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    def test_display_amount_last_payment(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None
        last_payment = Transaction({"money_out": 234, "id":12})
        mock_last_payment.return_value = last_payment

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 234)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_default(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_money_in(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.transaction_type = 'money_in'

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount_renewal_first_payment(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,3,1),
                    'first_payment': 456,
                    'amount': 789
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 456)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount_renewal_regular_amount(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'renewal': {
                    'date': datetime.date(2024,2,28),
                    'first_payment': 456,
                    'amount': 789
                },
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 789)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 24.6)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_last_date_overrides(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.config = {
            'last_date_overrides': {
                'payment': {
                    datetime.date(2024,2,1): datetime.date(2024,2,23)
                }
            }
        }

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, datetime.date(2024,2,23))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    def test_last_date_no_desc(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        t = Transaction({
            'id': 123,
            'date': datetime.date(2024,2,22)
        })
        mock_last_payment.return_value = t

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    def test_last_date_last_payment(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        t = Transaction({
            'id': 123,
            'date': datetime.date(2024,2,22)
        })
        mock_last_payment.return_value = t

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, datetime.date(2024,2,22))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_payment', new_callable=PropertyMock)
    @patch('monzo_utils.model.finance.Finance.older_last_payment', new_callable=PropertyMock)
    def test_last_date_older_last_payment(self, mock_older_last_payment, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        t = Transaction({
            'id': 123,
            'date': datetime.date(2024,2,22)
        })
        mock_last_payment.return_value = None
        mock_older_last_payment.return_value = t

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, datetime.date(2024,2,22))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_last_date_return_from_cache(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.cache['last_date'] = datetime.date(2024,2,22)

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, datetime.date(2024,2,22))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__desc_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': ['desc1', 'desc2'],
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s  or  description like %s )')
            self.assertEqual(params, [0, 0, '%desc1%', '%desc2%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__desc_single(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s )')
            self.assertEqual(params, [0, 0, '%desc1%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__start_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and `date` >= %s')
            self.assertEqual(params, [0, 0, '%desc1%', '2024-01-01'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__fixed(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'fixed': True,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and `date` >= %s and money_out = %s')
            self.assertEqual(params, [0, 0, '%desc1%', '2024-01-01', 123])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__fixed_amounts_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'fixed': True,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition([123,234,456])

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and `date` >= %s and ( money_out = %s or  money_out = %s or  money_out = %s)')
            self.assertEqual(params, [0, 0, '%desc1%', '2024-01-01', 123, 234, 456])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__not_fixed_amounts_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition([123,234,456])

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and `date` >= %s and ( money_out = %s or  money_out = %s or  money_out = %s)')
            self.assertEqual(params, [0, 0, '%desc1%', '2024-01-01', 123, 234, 456])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_last_payment_no_transactions(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]
        mock_find.return_value = []

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.last_payment

        self.assertEqual(resp, None)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_last_payment_skip_if_start_date_not_reached(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        transaction = Transaction({
            'id': 123,
            'date': datetime.date(2024,1,1)
        })

        mock_find.return_value = [transaction]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.last_payment

        self.assertEqual(resp, None)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_last_payment_return_first_matching_result(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        mock_find.return_value = [
            Transaction({
                'id': 123,
                'date': datetime.date(2024,1,1)
            }),
            Transaction({
                'id': 234,
                'date': datetime.date(2024,1,2)
            }),
            Transaction({
                'id': 456,
                'date': datetime.date(2024,1,3)
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.last_payment

        self.assertIsInstance(resp, Transaction)
        self.assertEqual(resp.id, 234)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_last_payment_return_from_cache(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        mock_find.return_value = [
            Transaction({
                'id': 123,
                'date': datetime.date(2024,1,1)
            }),
            Transaction({
                'id': 234,
                'date': datetime.date(2024,1,2)
            }),
            Transaction({
                'id': 456,
                'date': datetime.date(2024,1,3)
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.cache['last_payment'] = Transaction({
            'id': 456,
            'date': datetime.date(2024,1,3)
        })

        resp = p.last_payment

        self.assertIsInstance(resp, Transaction)
        self.assertEqual(resp.id, 456)



    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_older_last_payment_no_transactions(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]
        mock_find.return_value = []

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,1),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.older_last_payment

        self.assertEqual(resp, None)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_older_last_payment_dont_skip_if_start_date_not_reached(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        transaction = Transaction({
            'id': 123,
            'date': datetime.date(2024,1,1)
        })

        mock_find.return_value = [transaction]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.older_last_payment

        self.assertIsInstance(resp, Transaction)
        self.assertEqual(resp.id, 123)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_older_last_payment_return_first_matching_result(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        mock_find.return_value = [
            Transaction({
                'id': 123,
                'date': datetime.date(2024,1,1)
            }),
            Transaction({
                'id': 234,
                'date': datetime.date(2024,1,2)
            }),
            Transaction({
                'id': 456,
                'date': datetime.date(2024,1,3)
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.cache = {}

        resp = p.older_last_payment

        self.assertIsInstance(resp, Transaction)
        self.assertEqual(resp.id, 123)

        mock_get_transaction_where_condition.assert_called()

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at desc', [12])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    def test_older_last_payment_return_from_cache(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        mock_find.return_value = [
            Transaction({
                'id': 123,
                'date': datetime.date(2024,1,1)
            }),
            Transaction({
                'id': 234,
                'date': datetime.date(2024,1,2)
            }),
            Transaction({
                'id': 456,
                'date': datetime.date(2024,1,3)
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,1,2),
                'fixed': False,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.cache['older_last_payment'] = Transaction({
            'id': 456,
            'date': datetime.date(2024,1,3)
        })

        resp = p.older_last_payment

        self.assertIsInstance(resp, Transaction)
        self.assertEqual(resp.id, 456)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_due_date__yearly_month(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'yearly_month': 8,
                'yearly_day': 22,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.due_date, datetime.date(2024,8,22))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_due_date__renew_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'renew_date': datetime.date(2024,5,1),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.due_date, datetime.date(2024,5,1))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_due_date__start_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,5,1),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.due_date, datetime.date(2024,5,1))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_due_date__no_last_date_or_start_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.due_date, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_date', new_callable=PropertyMock)
    def test_due_date__calculate_from_last_date(self, mock_last_date, mock_query, mock_db):
        mock_db.return_value = None

        mock_last_date.return_value = datetime.date(2024,4,1)

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_date, datetime.date(2024,5,1))

        mock_last_date.return_value = datetime.date(2023,12,28)

        self.assertEqual(p.due_date, datetime.date(2024,1,28))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_date', new_callable=PropertyMock)
    def test_due_date__calculate_from_last_date_with_start_date(self, mock_last_date, mock_query, mock_db):
        mock_db.return_value = None

        mock_last_date.return_value = datetime.date(2023,12,28)

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,2,2),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_date, datetime.date(2024,2,2))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.last_date', new_callable=PropertyMock)
    def test_due_date__calculate_from_last_date_with_exclude_months(self, mock_last_date, mock_query, mock_db):
        mock_db.return_value = None

        mock_last_date.return_value = datetime.date(2023,12,28)

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'exclude_months': [1,2,3,4,5,6,7,8,9],
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_date, datetime.date(2024,10,28))

        mock_last_date.return_value = datetime.date(2023,11,28)

        p.payment_config['exclude_months'] = [12]

        self.assertEqual(p.due_date, datetime.date(2024,1,28))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_due_next_month_renew_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'renew_date': datetime.date(2024,3,31),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)

        p.payment_config['renew_date'] = datetime.date(2024,4,1)

        self.assertEqual(p.due_next_month, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.due_date', new_callable=PropertyMock)
    def test_due_next_month_start_date(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'start_date': datetime.date(2024,3,31),
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)

        p.payment_config['start_date'] = datetime.date(2024,4,1)

        self.assertEqual(p.due_next_month, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.due_date', new_callable=PropertyMock)
    def test_due_next_month_due_date_null(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = None

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.due_date', new_callable=PropertyMock)
    def test_due_next_month_final_condition(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = datetime.date(2024,3,31)

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)

        mock_due_date.return_value = datetime.date(2024,4,1)

        self.assertEqual(p.due_next_month, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.due_date', new_callable=PropertyMock)
    def test_yearly_payment_due_this_month(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = datetime.date(2024,3,31)

        p = Finance(
            {
                'salary_payment_day': 1
            },
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'yearly_month': 2,
                'yearly_day': 3,
                'months': 5
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.yearly_payment_due_this_month(), True)

        p.payment_config['yearly_month'] = 3

        self.assertEqual(p.yearly_payment_due_this_month(), False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    @patch('monzo_utils.model.transaction.Transaction.find')
    def test_all_finance_transactions__single_payment(self, mock_find, mock_get_transaction_where_condition, mock_query, mock_db):
        mock_db.return_value = None

        mock_get_transaction_where_condition.return_value = 'blah = %s', [2]
        mock_find.return_value = ['data']

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5,
                'single_payment': True
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.all_finance_transactions

        self.assertEqual(resp, ['data'])

        mock_get_transaction_where_condition.assert_called_with(amounts=False)

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at asc', [2])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.get_transaction_where_condition')
    @patch('monzo_utils.model.transaction.Transaction.find')
    def test_all_finance_transactions__no_single_payment(self, mock_find, mock_get_transaction_where_condition, mock_query, mock_db):
        mock_db.return_value = None

        mock_get_transaction_where_condition.return_value = 'blah = %s', [2]
        mock_find.return_value = ['data']

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5,
                'single_payment': False
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.all_finance_transactions

        self.assertEqual(resp, ['data'])

        mock_get_transaction_where_condition.assert_called_with([24.6])

        mock_find.assert_called_with('select * from transaction where blah = %s order by created_at asc', [2])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.all_finance_transactions', new_callable=PropertyMock)
    def test_total_paid(self, mock_all_finance_transactions, mock_query, mock_db):
        mock_db.return_value = None

        mock_all_finance_transactions.return_value = [
            Transaction({
                'id': 12,
                'money_out': 23.2
            }),
            Transaction({
                'id': 12,
                'money_out': 31.7
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5,
                'single_payment': False
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.total_paid, 54.9)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.all_finance_transactions', new_callable=PropertyMock)
    def test_num_paid(self, mock_all_finance_transactions, mock_query, mock_db):
        mock_db.return_value = None

        mock_all_finance_transactions.return_value = [
            Transaction({
                'id': 12,
                'money_out': 23.2
            }),
            Transaction({
                'id': 12,
                'money_out': 31.7
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5,
                'single_payment': False
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.num_paid, 2)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.finance.Finance.all_finance_transactions', new_callable=PropertyMock)
    def test_remaining(self, mock_all_finance_transactions, mock_query, mock_db):
        mock_db.return_value = None

        mock_all_finance_transactions.return_value = [
            Transaction({
                'id': 12,
                'money_out': 23.2
            }),
            Transaction({
                'id': 12,
                'money_out': 31.7
            })
        ]

        p = Finance(
            {},
            'payment_list_config',
            {
                'name': 'payment',
                'amount': 123,
                'desc': 'desc1',
                'months': 5,
                'single_payment': False
            },
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.remaining, 68.1)
