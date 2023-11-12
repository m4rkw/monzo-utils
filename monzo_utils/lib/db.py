import MySQLdb
import re
import sys
import os
import json
import datetime
import importlib
from monzo_utils.lib.singleton import Singleton
from monzo_utils.lib.config import Config

class DB(metaclass=Singleton):

    def __init__(self, db_config=None):
        if db_config:
            self.config = db_config
        else:
            self.config = Config().db

        self.driver = getattr(importlib.import_module(f"monzo_utils.lib.db_driver.{self.config['driver']}"), self.config['driver'])(self.config)

        self.columns = {}


    def __getattr__(self, name):
        match = re.match('^find_([\w]+)_by_(.*?)$', name)

        if match:
            table = match.group(1)

            if table[0:4] == 'all_':
                table = table[4:]
                find_all = True
            else:
                find_all = False

            fields = match.group(2).split('_and_')

            def find_object_by_fields(*args, **kwargs):
                sql = "select * from `" + table + "` where ("

                sql_args = []

                for i in range(0, len(fields)):
                    if i >0:
                        sql += " and "

                    if type(args[i]) == list:
                        sql += "("
                        for j in range(0, len(args[i])):
                            if j >0:
                                sql += " or "

                            if 'search' in kwargs and type(kwargs['search']) == list and fields[i] in kwargs['search']:
                                sql += f"`{fields[i]}` like %s"
                                sql_args.append('%' + args[i][j] + '%')
                            else:
                                sql += f"`{fields[i]}` = %s"
                                sql_args.append(args[i][j])

                        sql += ")"
                    else:
                        if 'search' in kwargs and type(kwargs['search']) == list and fields[i] in kwargs['search']:
                            sql += "`" + fields[i] + "` like %s"
                            sql_args.append('%' + args[i] + '%')
                        else:
                            sql += "`" + fields[i] + "` = %s"
                            sql_args.append(args[i])

                sql += ")"

                if 'where' in kwargs:
                    for where_clause in kwargs['where']:
                        sql += f" and {where_clause['clause']}"

                        if 'params' in where_clause:
                            sql_args += where_clause['params']

                if 'orderby' in kwargs:
                    sql += f" order by {kwargs['orderby']}"

                    if 'orderdir' in kwargs:
                        sql += f" {kwargs['orderdir']}"

                if 'limit' in kwargs:
                    sql += f" limit {kwargs['limit']}"

                if find_all:
                    return self.query(sql, sql_args)
                else:
                    return self.one(sql, sql_args)

            return find_object_by_fields
        else:
            print("DB class method missing: %s" % (name))
            sys.exit(1)


    def json_params(self, params):
        json_params = []

        for param in params:
            if type(param) == datetime.date:
                json_params.append(param.strftime('%Y-%M-%d'))
            elif type(param) == datetime.datetime:
                json_params.append(param.strftime('%Y-%M-%d %H:%M:%S'))
            else:
                json_params.append(param)

        return json_params


    def query(self, sql, params=[]):
        if 'DEBUG' in os.environ and os.environ['DEBUG'] == '1':
            print("SQL: %s" % (sql))
            print("PARAMS: %s" % (json.dumps(self.json_params(params),indent=4)))

        result = self.driver.query(sql, params)

        if type(result) == list:
            rows = []

            for row in result:
                rows.append(self.fix_dates(row))

            result = rows

        return result


    def fix_dates(self, row):
        fixed_row = {}

        for key in row:
            if type(row[key]) == str:
                m = re.match('^([\d]{4})-([\d]{2})-([\d]{2})$', row[key])

                if m:
                    fixed_row[key] = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    continue

                m = re.match('^([\d]{4})-([\d]{2})-([\d]{2}) ([\d]{2}):([\d]{2}):([\d]{2})$', row[key])

                if m:
                    fixed_row[key] = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                    continue

            fixed_row[key] = row[key]

        return fixed_row


    def one(self, sql, params=[]):
        rows = self.query(sql, params)

        if len(rows) >0:
            return rows[0]

        return False


    def find(self, table):
        self.query_table = table
        self.sel = []
        self.whereClauses = []
        self.whereParams = []
        self.andWhereClauses = []
        self._orderBy = None
        self._orderDir = None
        self._join = []
        self._leftJoin = []
        self._groupBy = None

        return self


    def select(self, select):
        self.sel.append(select)

        return self


    def where(self, where, whereParams):
        self.whereClauses.append(where)
        self.whereParams += whereParams

        return self


    def andWhere(self, where, whereParams):
        self.andWhereClauses.append(where)
        self.whereParams += whereParams

        return self


    def orderBy(self, field, direction='asc'):
        self._orderBy = field
        self._orderDir = direction

        return self


    def join(self, join_table, join_left_col, join_right_col=None):
        if join_right_col:
            self._join.append({
                'table': join_table,
                'join_left_col': join_left_col,
                'join_right_col': join_right_col
            })
        else:
            self._join.append({
                'table': join_table,
                'clause': join_left_col
            })

        return self


    def leftJoin(self, join_table, join_left_col, join_right_col, where=None):
        self._leftJoin.append({
            'table': join_table,
            'join_left_col': join_left_col,
            'join_right_col': join_right_col,
            'where': where
        })

        return self


    def orWhere(self, whereClause, whereParams=[]):
        self.whereType = 'or'

        return self.where(whereClause, whereParams)


    def groupBy(self, groupBy):
        self._groupBy = groupBy

        return self


    def prepare(self):
        if self.sel == []:
            select = '*'
        else:
            select = ''

            for i in range(0, len(self.sel)):
                if i >0:
                    select += ','
                select += f"{self.sel[i]}"

        sql = "select " + select + " from `" + self.query_table + "`"

        for join in self._join:
            sql += " join `" + join['table'] + "` on "

            if 'clause' in join:
                sql += join['clause']
            else:
                sql += join['join_left_col'] + " = " + join['join_right_col']

        for join in self._leftJoin:
            sql += " left join `" + join['table'] + "` on "

            if 'clause' in join:
                sql += join['clause']
            else:
                sql += join['join_left_col'] + " = " + join['join_right_col']

        if len(self.whereClauses) >0:
            sql += " where ("

            for i in range(0, len(self.whereClauses)):
                if i >0:
                    sql += " or "
                sql += self.whereClauses[i]

            sql += ")"

            for i in range(0, len(self.andWhereClauses)):
                sql += " and (" + self.andWhereClauses[i] + ") "

        if self._groupBy:
            sql += " group by " + self._groupBy

        if self._orderBy:
            sql += " order by "
            order_by_fields = self._orderBy.split(',')

            for i in range(0, len(order_by_fields)):
                if i >0:
                    sql += ","
                sql += f" `{order_by_fields[i].strip()}`"

        if self._orderDir:
            sql += " " + self._orderDir

        return sql


    def getone(self):
        sql = self.prepare() + " limit 1"

        return self.one(sql, self.whereParams)


    def getall(self):
        rows = []

        for row in self.query(self.prepare(), self.whereParams):
            rows.append(row)

        return rows


    def get_raw_query(self):
        sql = self.prepare()

        raw_sql = ''

        n = 0
        skip = False

        for i in range(0, len(sql)):
            if skip:
                skip = False
                continue

            if sql[i:i+2] == '%s':
                raw_sql += "'" + self.whereParams[n] + "'"
                n += 1
                skip = True
            else:
                raw_sql += sql[i]

        return raw_sql


    def update(self, table, _id, data):
        if table not in self.columns:
            self.columns[table] = self.driver.get_columns(table, exclude=['id'])

        sql = f"update `{table}` set"
        params = []

        for i in range(0, len(self.columns[table])):
            if i >0:
                sql += ", "

            sql += f" `{self.columns[table][i]}` = %s"
            params.append(data[self.columns[table][i]] if self.columns[table][i] in data else None)

        sql += f" where `id` = %s"
        params.append(_id)

        self.query(sql, params)


    def create(self, table, data):
        if table not in self.columns:
            self.columns[table] = self.driver.get_columns(table, exclude=['id'])

        sql = f"insert into `{table}` ("
        params = []

        for i in range(0, len(self.columns[table])):
            if i >0:
                sql += ","

            sql += f"`{self.columns[table][i]}`"
            params.append(data[self.columns[table][i]] if self.columns[table][i] in data else None)

        sql += f") VALUES ("

        for i in range(0, len(self.columns[table])):
            if i >0:
                sql += ","
            sql += "%s"

        sql += ")"

        return self.query(sql, params)
