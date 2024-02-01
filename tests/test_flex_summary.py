from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from monzo_utils.model.flex_summary import FlexSummary
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.lib.transactions_seen import TransactionsSeen
import pytest
import datetime
import decimal
import json
from freezegun import freeze_time

class TestFlex(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}
        TransactionsSeen().seen = {}


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_constructor(self, mock_query, mock_init):
        with freeze_time("2024-01-01"):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.config, {
                'flex_payment_date':1,
                'flex_account': 'Current'
            })
            self.assertEqual(p.flex_total, 1100.1)
            self.assertEqual(p.flex_total_next_month, 635.4)
            self.assertEqual(p.flex_remaining, 800.1)
            self.assertEqual(p.last_salary_date, datetime.date(2024,2,1))
            self.assertEqual(p.next_salary_date, datetime.date(2024,3,1))
            self.assertEqual(p.following_salary_date, datetime.date(2024,4,1))

            self.assertEqual(p.cache, {})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_data_fields(self, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
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

        self.assertEqual(data['amount'], 1100.1)
        self.assertEqual(data['due_date'], datetime.date(2024, 2, 1))
        self.assertEqual(data['last_date'], datetime.date(2024, 1, 1))
        self.assertEqual(data['name'], 'Flex Payment')
        self.assertEqual(data['payment_type'], 'Flex Summary')
        self.assertEqual(data['remaining'], 800.1)
        self.assertEqual(data['status'], 'DUE')
        self.assertEqual(data['suffix'], '')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_data_abbreviated(self, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
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

        self.assertEqual(data['amount'], 1100.1)
        self.assertEqual(data['due_date'], '01/02/24')
        self.assertEqual(data['last_date'], '01/01/24')
        self.assertEqual(data['name'], 'Flex Payment')
        self.assertEqual(data['payment_type'], 'FS')
        self.assertEqual(data['remaining'], 800.1)
        self.assertEqual(data['status'], 'DUE')
        self.assertEqual(data['suffix'], '')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_abbreviate(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.abbreviate('Test One Two Three'), 'TOTT')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_short_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.short_date(None), None)
        self.assertEqual(p.short_date(datetime.date(2024,1,1)), '01/01/24')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('builtins.print')
    def test_display(self, mock_print, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            p.display()

        mock_print.assert_called_with('    DUE: Flex Summary    Flex Payment                    £1100.10 ->£635.40  £800.10  2024-01-01   2024-02-01')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('builtins.print')
    def test_display_last_amount_override(self, mock_print, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            p.cache['last_payment'] = Transaction()
            p.cache['last_payment'].id = 123
            p.cache['last_payment'].money_out = 123
            p.cache['last_payment'].date = datetime.date(2024,2,2)

            p.display()

            mock_print.assert_called_with('   PAID: Flex Summary    Flex Payment                    £1100.10 ->£635.40  £800.10  2024-02-02   2024-04-01')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_name(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.name, 'Flex Payment')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_status_due(self, mock_query, mock_db):
        mock_db.return_value = None

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.last_payment', new_callable=PropertyMock)
    def test_status_paid(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        t = Transaction({
            'id':1,
            'date': datetime.date(2024,1,31)
        })

        mock_last_payment.return_value = t

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            t = Transaction({
                'id':1,
                'date': datetime.date(2024,2,1)
            })

            mock_last_payment.return_value = t

            self.assertEqual(p.status, 'PAID')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.last_payment', new_callable=PropertyMock)
    def test_status_last_payment(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        t = Transaction({'id':1,'date':datetime.date(2024,1,31)})

        mock_last_payment.return_value = t

        with freeze_time('2024-01-22'):
            p = FlexSummary(
                {
                    'flex_payment_date':1,
                    'flex_account': 'Current',
                },
                1100.10,
                635.4,
                800.1,
                datetime.date(2024,2,1),
                datetime.date(2024,3,1),
                datetime.date(2024,4,1),
            )

            self.assertEqual(p.status, 'DUE')

            t = Transaction({'id':1,'date':datetime.date(2024,2,1)})

            mock_last_payment.return_value = t

            self.assertEqual(p.status, 'PAID')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_payment_type(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.payment_type, 'Flex Summary')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_num_paid(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.num_paid, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_num_total(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.num_total, None)

        p.payment_config['months'] = 3

        self.assertEqual(p.num_total, 3)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_remaining(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.remaining, 800.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_override(self, mock_query, mock_db):
        mock_db.return_value = None

        config = Config({
            'last_amount_overrides': {
                'payment': {
                    datetime.date(2024,2,1): 456
                }
            }
        })

        Config._instances = {Config: config}

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.display_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.last_payment', new_callable=PropertyMock)
    def test_display_amount_last_payment(self, mock_last_payment, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None
        last_payment = Transaction({"money_out": 234, "id":12})
        mock_last_payment.return_value = last_payment

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_default(self, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_display_amount_money_in(self, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.transaction_type = 'money_in'

        with freeze_time("2024-01-20"):
            self.assertEqual(p.display_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount_renewal_first_payment(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount_renewal_regular_amount(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_next_month_amount(self, mock_query, mock_db):
        mock_config = MagicMock()
        Config._instances[Config] = mock_config

        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.next_month_amount, 1100.1)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.last_payment', new_callable=PropertyMock)
    def test_last_date_last_payment(self, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    @patch('monzo_utils.model.flex_summary.FlexSummary.last_payment', new_callable=PropertyMock)
    @patch('monzo_utils.model.flex_summary.FlexSummary.older_last_payment', new_callable=PropertyMock)
    def test_last_date_older_last_payment(self, mock_older_last_payment, mock_last_payment, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
            self.assertEqual(p.last_date, datetime.date(2024,1,1))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_last_date_return_from_cache(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )
        p.cache['last_date'] = datetime.date(2024,2,22)

        with freeze_time("2024-01-20"):
            self.assertEqual(p.last_date, datetime.date(2024,1,1))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__desc_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s )')
            self.assertEqual(params, [0, 0, '%FlexSummary%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__desc_single(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s )')
            self.assertEqual(params, [0, 0, '%FlexSummary%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__start_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s )')
            self.assertEqual(params, [0, 0, '%FlexSummary%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__fixed(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition()

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s )')
            self.assertEqual(params, [0, 0, '%FlexSummary%'])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__fixed_amounts_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition([123,234,456])

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and ( money_out = %s or  money_out = %s or  money_out = %s)')
            self.assertEqual(params, [0, 0, '%FlexSummary%', 123, 234, 456])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_get_transaction_where_condition__not_fixed_amounts_list(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            where, params = p.get_transaction_where_condition([123,234,456])

            self.assertEqual(where, 'money_out > %s and declined = %s and (  description like %s ) and ( money_out = %s or  money_out = %s or  money_out = %s)')
            self.assertEqual(params, [0, 0, '%FlexSummary%', 123, 234, 456])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.__init__')
    def test_last_payment_no_transactions(self, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_find.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        resp = p.last_payment

        self.assertEqual(resp, None)

        mock_find.assert_called_with('select * from transaction where account_id = %s and declined = %s and money_in = %s and description = %s and `date` > %s order by created_at asc limit 1', [None, 0, 1100.1, 'Flex', datetime.date(2024, 2, 1)])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.transaction.Transaction.find')
    @patch('monzo_utils.model.flex_summary.FlexSummary.get_transaction_where_condition')
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

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    @patch('monzo_utils.model.flex_summary.FlexSummary.get_transaction_where_condition')
    def test_older_last_payment_no_transactions(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]
        mock_find.return_value = []

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    @patch('monzo_utils.model.flex_summary.FlexSummary.get_transaction_where_condition')
    def test_older_last_payment_dont_skip_if_start_date_not_reached(self, mock_get_transaction_where_condition, mock_find, mock_query, mock_db):
        mock_db.return_value = None
        mock_get_transaction_where_condition.return_value = 'blah = %s', [12]

        transaction = Transaction({
            'id': 123,
            'date': datetime.date(2024,1,1)
        })

        mock_find.return_value = [transaction]

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    @patch('monzo_utils.model.flex_summary.FlexSummary.get_transaction_where_condition')
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

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    @patch('monzo_utils.model.flex_summary.FlexSummary.get_transaction_where_condition')
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

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
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
    def test_due_date__start_date(self, mock_query, mock_db):
        mock_db.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        with freeze_time("2024-01-20"):
            self.assertEqual(p.due_date, datetime.date(2024,2,1))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.due_date', new_callable=PropertyMock)
    def test_due_next_month_start_date(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)

        p.payment_config['start_date'] = datetime.date(2024,4,1)

        self.assertEqual(p.due_next_month, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.due_date', new_callable=PropertyMock)
    def test_due_next_month_due_date_null(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = None

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    @patch('monzo_utils.model.flex_summary.FlexSummary.due_date', new_callable=PropertyMock)
    def test_due_next_month_final_condition(self, mock_due_date, mock_query, mock_db):
        mock_db.return_value = None
        mock_due_date.return_value = datetime.date(2024,3,31)

        p = FlexSummary(
            {
                'flex_payment_date':1,
                'flex_account': 'Current',
            },
            1100.10,
            635.4,
            800.1,
            datetime.date(2024,2,1),
            datetime.date(2024,3,1),
            datetime.date(2024,4,1),
        )

        self.assertEqual(p.due_next_month, True)

        mock_due_date.return_value = datetime.date(2024,4,1)

        self.assertEqual(p.due_next_month, False)
