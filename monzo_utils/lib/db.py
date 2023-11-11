import MySQLdb
import re
import sys
import os
import json
import datetime
from monzo_utils.lib.singleton import Singleton

class DB(metaclass=Singleton):

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


    def __init__(self, config):
        self.config = config
        self.columns = {}


    def connect(self):
        self.db = MySQLdb.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            passwd=self.config['password'],
            db=self.config['database'],
            charset='utf8',
            use_unicode=True,
            ssl={}
        )
        self.cur = self.db.cursor()


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

        self.connect()
        self.cur.execute((sql), params)

        if sql[0:6].lower() == "select":
            self.db.commit()
            return self.build_rows(self.cur.fetchall())

        self.db.commit()

        return None


    def one(self, sql, params=[]):
        rows = self.query(sql, params)

        if len(rows) >0:
            return rows[0]

        return False


    def build_row(self, data):
        row = {}

        for i in range(0, len(self.cur.description)):
            row[self.cur.description[i][0]] = data[i]

        return row


    def build_rows(self, data):
        rows = []

        for item in data:
            rows.append(self.build_row(item))

        return rows


    def find(self, table):
        self.sel = '*'
        self.query_table = table
        self.whereClauses = []
        self.whereParams = []
        self.whereType = 'and'
        self.orderBy = None
        self.orderDir = None
        self._join = []
        self._leftJoin = []

        return self


    def select(self, select_str):
        self.sel = select_str

        return self


    def where(self, where, *whereParams):
        self.whereClauses.append(where)
        self.whereParams += whereParams

        return self


    def orderby(self, field, direction='asc'):
        self.orderBy = field
        self.orderDir = direction

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


    def leftJoin(self, join_table, join_left_col, join_right_col=None):
        if join_right_col:
            self._leftJoin.append({
                'table': join_table,
                'join_left_col': join_left_col,
                'join_right_col': join_right_col
            })
        else:
            self._leftJoin.append({
                'table': join_table,
                'clause': join_left_col
            })

        return self


    def orWhere(self, whereClause, whereParams=[]):
        self.whereType = 'or'

        return self.where(whereClause, whereParams)


    def prepare(self):
        sql = "select " + self.sel + " from `" + self.query_table + "`"

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

        for i in range(0, len(self.whereClauses)):
            if i >0:
                sql += " " + self.whereType + " "
            else:
                sql += " where "

            sql += self.whereClauses[i]

        if self.orderBy:
            sql += " order by `" + self.orderBy + "`"

        if self.orderDir:
            sql += " " + self.orderDir

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


    def get_columns(self, table):
        columns = []

        for row in self.query("select column_name from information_schema.columns where table_schema = %s and table_name = %s", [self.config['database'], table]):
            if row['column_name'] != 'id':
                columns.append(row['column_name'])

        return columns


    def update(self, table, _id, data):
        if table not in self.columns:
            self.columns[table] = self.get_columns(table)

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
            self.columns[table] = self.get_columns(table)

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

        self.query(sql, params)

        return self.one(f"select `id` from `{table}` order by `id` desc limit 1")['id']
