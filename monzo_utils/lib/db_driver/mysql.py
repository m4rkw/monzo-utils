import MySQLdb
import re
import sys
import os
import json
import datetime
from monzo_utils.lib.singleton import Singleton
from monzo_utils.lib.config import Config

class mysql:

    def __init__(self, config):
        self.config = config
        self.columns = {}
        self.connect()


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


    def query(self, sql, params=[]):
        if 'DEBUG' in os.environ and os.environ['DEBUG'] == '1':
            print("SQL: %s" % (sql))
            print("PARAMS: %s" % (json.dumps(self.json_params(params),indent=4)))

        self.cur.execute((sql), params)

        if sql[0:6].lower() == "select":
            self.db.commit()
            return self.build_rows(self.cur.fetchall())

        self.db.commit()

        if sql[0:6].lower() == "insert":
            return self.cur.lastrowid

        return None


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


    def get_columns(self, table):
        columns = []

        for row in self.query("select column_name from information_schema.columns where table_schema = %s and table_name = %s", [self.config['database'], table]):
            if row['column_name'] != 'id':
                columns.append(row['column_name'])

        return columns
