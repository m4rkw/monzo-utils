from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from monzo_utils.lib.db import DB
from monzo_utils.lib.db_driver.mysql import mysql
import datetime

class TestDB(BaseTest):

    def setUp(self):
        DB._instances = {}


    @patch('monzo_utils.lib.db_driver.mysql.mysql.__init__')
    def test_constructor_config_provided(self, mock_mysql):
        mock_mysql.return_value = None

        config = {
            'driver': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'password',
            'database': 'monzo'
        }

        db = DB(config)

        self.assertEqual(db.config, config)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_json_params(self, mock_init):
        mock_init.return_value = None

        db = DB()

        params = [
            datetime.date(2024,1,1),
            datetime.datetime(2024,2,1,12,1,1),
            'test',
            134,
            11.1
        ]

        json_params = db.json_params(params)

        self.assertEqual(json_params, [
            '2024-01-01',
            '2024-02-01 12:01:01',
            'test',
            134,
            11.1
        ])


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_query_not_list(self, mock_init):
        mock_init.return_value = None

        db = DB()
        db.driver = MagicMock()
        db.driver.query.return_value = None

        resp = db.query('select * from blah where id = %s', [123])

        db.driver.query.assert_called_with('select * from blah where id = %s', [123])

        self.assertEqual(resp, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_query_list(self, mock_init):
        mock_init.return_value = None

        db = DB()
        db.driver = MagicMock()
        db.driver.query.return_value = [
            {
                'key1': '2024-01-01',
                'key2': '2024-02-02 12:11:11',
                'key3': 'blah'
            }
        ]

        resp = db.query('select * from blah where id = %s', [123])

        db.driver.query.assert_called_with('select * from blah where id = %s', [123])

        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)
        self.assertIsInstance(resp[0], dict)
        self.assertIn('key1', resp[0])
        self.assertIn('key2', resp[0])
        self.assertIn('key3', resp[0])
        self.assertEqual(resp[0]['key1'], datetime.date(2024,1,1))
        self.assertEqual(resp[0]['key2'], datetime.datetime(2024,2,2,12,11,11))
        self.assertEqual(resp[0]['key3'], 'blah')


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_fix_dates_date(self, mock_init):
        mock_init.return_value = None

        db = DB()

        fixed_row = db.fix_dates({
            'key1': '2024-01-01'
        })

        self.assertEqual(fixed_row, {'key1': datetime.date(2024,1,1)})


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_fix_dates_datetime(self, mock_init):
        mock_init.return_value = None

        db = DB()

        fixed_row = db.fix_dates({
            'key1': '2024-01-01 12:12:12'
        })

        self.assertEqual(fixed_row, {'key1': datetime.datetime(2024,1,1,12,12,12)})


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_one_not_found(self, mock_query, mock_init):
        mock_init.return_value = None
        mock_query.return_value = []

        db = DB()

        resp = db.one("select * from blah where id = %s", [123])

        mock_query.assert_called_with('select * from blah where id = %s', [123])

        self.assertEqual(resp, False)


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_one_found(self, mock_query, mock_init):
        mock_init.return_value = None
        mock_query.return_value = [
            {
                'one': 'two'
            }
        ]

        db = DB()

        resp = db.one("select * from blah where id = %s", [123])

        mock_query.assert_called_with('select * from blah where id = %s', [123])

        self.assertEqual(resp, {'one': 'two'})


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_find(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, [])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [])
        self.assertEqual(db.andWhereClauses, [])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_select(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [])
        self.assertEqual(db.andWhereClauses, [])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)

        resp = db.select('select clause')

        self.assertEqual(resp, db)

        self.assertEqual(db.sel, ['select clause','select clause'])


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_where(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.where('where clause', [123])

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, ['where clause'])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, [])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)

        resp = db.where('where clause', [123])

        self.assertEqual(resp, db)

        self.assertEqual(db.whereClauses, ['where clause','where clause'])
        self.assertEqual(db.whereParams, [123,123])


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_and_where(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_order_by(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, 'field')
        self.assertEqual(db._orderDir, 'desc')
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_join_no_right_col(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, 'field')
        self.assertEqual(db._orderDir, 'desc')
        self.assertEqual(db._join, [{'clause': 'join left col', 'table': 'join table'}])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_join_right_col(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col', 'join right col')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, 'field')
        self.assertEqual(db._orderDir, 'desc')
        self.assertEqual(db._join, [{'join_left_col': 'join left col', 'join_right_col': 'join right col', 'table': 'join table'}])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_left_join_no_where(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col', 'join right col')
        resp = db.leftJoin('join table', 'join left col', 'join right col')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, 'field')
        self.assertEqual(db._orderDir, 'desc')
        self.assertEqual(db._join, [{'join_left_col': 'join left col', 'join_right_col': 'join right col', 'table': 'join table'}])
        self.assertEqual(db._leftJoin, [{'join_left_col': 'join left col', 'join_right_col': 'join right col', 'table': 'join table', 'where': None}])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_left_join_where(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col', 'join right col')
        resp = db.leftJoin('join table', 'join left col', 'join right col', 'blah = blah')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, [])
        self.assertEqual(db.whereParams, [123])
        self.assertEqual(db.andWhereClauses, ['where clause'])
        self.assertEqual(db._orderBy, 'field')
        self.assertEqual(db._orderDir, 'desc')
        self.assertEqual(db._join, [{'join_left_col': 'join left col', 'join_right_col': 'join right col', 'table': 'join table'}])
        self.assertEqual(db._leftJoin, [{'join_left_col': 'join left col', 'join_right_col': 'join right col', 'table': 'join table', 'where': 'blah = blah'}])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_or_where(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.orWhere('blah = %s', [555])

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, ['blah = %s'])
        self.assertEqual(db.whereParams, [555])
        self.assertEqual(db.andWhereClauses, [])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, None)


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_group_by(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.orWhere('blah = %s', [555])
        resp = db.groupBy('blah2')

        self.assertEqual(resp, db)

        self.assertEqual(db.query_table, 'mytable')
        self.assertEqual(db.sel, ['select clause'])
        self.assertEqual(db.whereClauses, ['blah = %s'])
        self.assertEqual(db.whereParams, [555])
        self.assertEqual(db.andWhereClauses, [])
        self.assertEqual(db._orderBy, None)
        self.assertEqual(db._orderDir, None)
        self.assertEqual(db._join, [])
        self.assertEqual(db._leftJoin, [])
        self.assertEqual(db._groupBy, 'blah2')


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_prepare(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col', 'join right col')
        resp = db.leftJoin('join table', 'join left col', 'join right col', 'blah = blah')
        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])
        resp = db.orderBy('field', 'desc')
        resp = db.join('join table', 'join left col', 'join right col')
        resp = db.leftJoin('join table', 'join left col', 'join right col', 'blah = blah')

        sql = db.prepare()

        self.assertEqual(sql, 'select select clause from `mytable` join `join table` on join left col = join right col left join `join table` on join left col = join right col order by  `field` desc')


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.one')
    def test_getone(self, mock_one, mock_init):
        mock_init.return_value = None
        mock_one.return_value = 'data'

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])

        resp = db.getone()

        self.assertEqual(resp, 'data')

        mock_one.assert_called_with('select select clause from `mytable` limit 1', [123])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_getall(self, mock_query, mock_init):
        mock_init.return_value = None
        mock_query.return_value = ['data']

        db = DB()

        resp = db.find('mytable')
        resp = db.select('select clause')
        resp = db.andWhere('where clause', [123])

        resp = db.getall()

        self.assertEqual(resp, ['data'])

        mock_query.assert_called_with('select select clause from `mytable`', [123])


    @patch('monzo_utils.lib.db.DB.__init__')
    def test_get_raw_query(self, mock_init):
        mock_init.return_value = None

        db = DB()

        resp = db.find('mytable')
        resp = db.select('mytable.*')
        resp = db.where('blah = %s and frog = %s', [123, 'test'])

        resp = db.get_raw_query()

        self.assertEqual(resp, "select mytable.* from `mytable` where (blah = 123 and frog = 'test')")


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_update(self, mock_query, mock_init):
        mock_init.return_value = None

        db = DB()
        db.driver = MagicMock()
        db.columns = {}

        db.driver.get_columns.return_value = ['id','key1','key2']

        resp = db.update('mytable', 123, {
            'key1': 'blah',
            'key2': 'bloo'
        })

        self.assertEqual(resp, None)

        mock_query.assert_called_with('update `mytable` set `id` = %s,  `key1` = %s,  `key2` = %s where `id` = %s', [None, 'blah', 'bloo', 123])


    @patch('monzo_utils.lib.db.DB.__init__')
    @patch('monzo_utils.lib.db.DB.query')
    def test_update(self, mock_query, mock_init):
        mock_init.return_value = None
        mock_query.return_value = 'query return'

        db = DB()
        db.driver = MagicMock()
        db.columns = {}

        db.driver.get_columns.return_value = ['id','key1','key2']

        resp = db.create('mytable', {
            'key1': 'blah',
            'key2': 'bloo'
        })

        self.assertEqual(resp, 'query return')

        mock_query.assert_called_with('insert into `mytable` (`id`,`key1`,`key2`) VALUES (%s,%s,%s)', [None, 'blah', 'bloo'])
