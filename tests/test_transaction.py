from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
import pytest
import datetime
import decimal
import json

class TestTransaction(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}


    def test_constructor(self):
        m = Transaction()

        self.assertEqual(m.attributes, {})
        self.assertEqual(m.table, 'transaction')
        self.assertEqual(m.factory_query, False)


    def test_constructor_with_data_dict(self):
        m = Transaction({
            'key': 'one',
            'key2': 'two'
        })

        self.assertEqual(m.attributes, {'key': 'one', 'key2': 'two'})
        self.assertEqual(m.table, 'transaction')
        self.assertEqual(m.factory_query, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.one')
    def test_one(self, mock_one, mock_db):
        mock_db.return_value = None
        mock_one.return_value = {
            'key': 'one',
            'key2': 'two'
        }
        m = Transaction.one("select * from account where id = %s", [123])

        self.assertIsInstance(m, Transaction)
        self.assertEqual(m.attributes, {'key': 'one', 'key2': 'two'})
        self.assertEqual(m.table, 'transaction')
        self.assertEqual(m.factory_query, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_find(self, mock_query, mock_init):
        mock_init.return_value = None
        mock_query.return_value = [{
            'key1': 'blah',
            'key2': 'bloo'
        }]

        m = Transaction()
        m.table = 'transaction'

        resp = m.find('select * from account where id = %s', [123])

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)
        self.assertIsInstance(resp[0], Transaction)
        self.assertEqual(resp[0].attributes, {'key1': 'blah', 'key2': 'bloo'})


    def test_getattr(self):
        m = Transaction({
            'key1': 'blah',
            'key2': 'bloo'
        })

        self.assertEqual(m.id, None)
        self.assertEqual(m.key1, 'blah')
        self.assertEqual(m.key2, 'bloo')

        with pytest.raises(AttributeError) as e:
            m.key3


    def test_bool_false(self):
        m = Transaction({
            'key1': 'blah',
            'key2': 'bloo'
        })

        self.assertEqual(bool(m), False)


    def test_bool_true(self):
        m = Transaction({
            'key1': 'blah',
            'key2': 'bloo',
            'id': 123
        })

        self.assertEqual(bool(m), True)


    def test_setattr_table(self):
        m = Transaction()

        m.table = 'account'

        self.assertEqual(m.attributes, {})
        self.assertEqual(m.table, 'account')


    def test_setattr_attributes(self):
        m = Transaction()

        m.attributes = {'one':'two'}

        self.assertEqual(m.attributes, {'one':'two'})


    def test_setattr_factory_query(self):
        m = Transaction()

        m.factory_query = True

        self.assertEqual(m.attributes, {})
        self.assertEqual(m.factory_query, True)


    def test_setattr_other_keys(self):
        m = Transaction()

        m.key1 = 'blah'
        m.key2 = 'blah'
        m.key3 = 'blah'

        self.assertEqual(m.attributes, {'key1': 'blah', 'key2': 'blah', 'key3': 'blah'})


    def test_delattr(self):
        m = Transaction()

        m.key1 = 'blah'

        self.assertEqual(m.attributes, {'key1': 'blah'})

        delattr(m, 'key1')

        self.assertEqual(m.attributes, {})


    def test_delattr_key_not_existing(self):
        m = Transaction()

        delattr(m, 'key1')

        self.assertEqual(m.attributes, {})


    def test_to_str(self):
        m = Transaction()

        self.assertEqual(str(m), '{}')

        m.attributes = {
            'blah': 'key1',
            'key2': datetime.date(2024,1,1),
            'key3': datetime.datetime(2024,1,1,12,13,13),
            'key': decimal.Decimal(12.222)
        }

        expected = {
            "blah": "key1",
            "key2": "2024-01-01",
            "key3": "2024-01-01 12:13:13",
            "key": 12.222
        }

        self.assertEqual(str(m), json.dumps(expected,indent=4))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_related(self, mock_query, mock_init):
        mock_init.return_value = None

        m = Transaction()

        m.related('transaction', 'account_id', 123, 'id', 'asc', None, 0)

        mock_query.assert_called_with('select * from `transaction` where account_id = %s and deleted = %s order by id asc', [123, 0])


    def test_update(self):
        m = Transaction()

        m.update({
            'key1': 'blah',
            'key2': 'bloo'
        })

        self.assertEqual(m.attributes, {'key1': 'blah', 'key2': 'bloo'})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.create')
    @patch('monzo_utils.lib.db.DB.update')
    def test_save_create_new(self, mock_update, mock_create, mock_init):
        mock_init.return_value = None

        m = Transaction()

        m.attributes = {
            'key1': 'blah',
            'key2': 'bloo'
        }

        m.save()

        mock_create.assert_called_with('transaction', {'key1': 'blah', 'key2': 'bloo'})
        mock_update.assert_not_called()


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.create')
    @patch('monzo_utils.lib.db.DB.update')
    def test_save_create_new(self, mock_update, mock_create, mock_init):
        mock_init.return_value = None

        m = Transaction()

        m.attributes = {
            'id': 123,
            'key1': 'blah',
            'key2': 'bloo'
        }

        m.save()

        mock_update.assert_called_with('transaction', 123, {'id': 123, 'key1': 'blah', 'key2': 'bloo'})
        mock_create.assert_not_called()


    def test_delete_without_id(self):
        mp = Transaction()

        with pytest.raises(Exception) as e:
            mp.delete()

        self.assertIn("Exception('Unable to delete record with null id')", str(e))


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_delete_with_id(self, mock_query, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        mp.attributes = {'id': 123}

        mp.delete()

        mock_query.assert_called_with('delete from transaction where id = %s', [123])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.find')
    def test_factory(self, mock_find, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        mp.factory_query = False
        mp.table = 'account'

        mp.factory()

        self.assertEqual(mp.factory_query, True)

        mock_find.assert_called_with('account')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.find')
    def test_factory_already_set(self, mock_find, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        mp.factory_query = True

        mp.factory()

        self.assertEqual(mp.factory_query, True)

        mock_find.assert_not_called()


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.select')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_select(self, mock_factory, mock_select, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        resp = mp.select('select clause')

        self.assertEqual(resp, mp)

        mock_factory.assert_called()
        mock_select.assert_called_with('select clause')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.join')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_join(self, mock_factory, mock_join, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        mp.RELATIONSHIPS = {
            'account': ['join column1', 'join column2']
        }

        resp = mp.join('account')

        mock_factory.assert_called()

        mock_join.assert_called_with('account', '`transaction`.account_id', 'account.id')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.leftJoin')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_left_join(self, mock_factory, mock_join, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        mp.RELATIONSHIPS = {
            'account': ['join column1', 'join column2']
        }

        resp = mp.leftJoin('account', 'blah = 1')

        mock_factory.assert_called()

        mock_join.assert_called_with('account', '`transaction`.account_id', 'account.id', 'blah = 1')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.where')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_select(self, mock_factory, mock_where, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        resp = mp.where('where blah = %s', [546])

        self.assertEqual(resp, mp)

        mock_factory.assert_called()
        mock_where.assert_called_with('where blah = %s', [546])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.andWhere')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_and_where(self, mock_factory, mock_where, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        resp = mp.andWhere('where blah = %s', [546])

        self.assertEqual(resp, mp)

        mock_factory.assert_called()
        mock_where.assert_called_with('where blah = %s', [546])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.groupBy')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_group_by(self, mock_factory, mock_group_by, mock_init):
        mock_init.return_value = None

        mp = Transaction()
        resp = mp.groupBy('blah')

        self.assertEqual(resp, mp)

        mock_factory.assert_called()
        mock_group_by.assert_called_with('blah')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.getall')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_getall(self, mock_factory, mock_getall, mock_init):
        mock_init.return_value = None
        mock_getall.return_value = ['data']

        mp = Transaction()
        resp = mp.getall()

        self.assertEqual(resp, ['data'])

        mock_factory.assert_called()
        mock_getall.assert_called_with()


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.getone')
    @patch('monzo_utils.model.transaction.Transaction.factory')
    def test_getone(self, mock_factory, mock_getone, mock_init):
        mock_init.return_value = None
        mock_getone.return_value = {'key1':'blah'}

        mp = Transaction()
        resp = mp.getone()

        self.assertEqual(resp, {'key1':'blah'})

        mock_factory.assert_called()
        mock_getone.assert_called_with()


    def test_display_keys(self):
        mp = Transaction()
        self.assertEqual(mp.DISPLAY_KEYS, ['date','type','money_in','money_out','pending','description'])


    def test_relationships__account(self):
        mp = Transaction()
        self.assertEqual(mp.RELATIONSHIPS['account'], ['`transaction`.account_id', 'account.id'])


    def test_relationships__transaction_metadata(self):
        mp = Transaction()
        self.assertEqual(mp.RELATIONSHIPS['transaction_metadata'], ['`transaction`.id', 'transaction_metadata.transaction_id'])


    def test_relationships__pot(self):
        mp = Transaction()
        self.assertEqual(mp.RELATIONSHIPS['pot'], ['`transaction`.pot_id', 'pot.id'])
