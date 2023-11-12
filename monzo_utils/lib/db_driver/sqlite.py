import sqlite3
import sys
import os

class sqlite:

    def __init__(self, config):
        self.config = config
        self.columns = {}
        self.connect()


    def connect(self):
        self.db = sqlite3.connect(self.config['path'])
        self.cur = self.db.cursor()


    def query(self, sql, params=[]):
        sql = sql.replace('%s', '?')

        result = self.cur.execute((sql), params)

        if sql[0:6].lower() in ['select','pragma']:
            self.db.commit()
            return self.build_rows(result.fetchall())

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


    def get_columns(self, table, exclude=None):
        columns = []

        for row in self.query(f"pragma table_info(`{table}`);"):
            if exclude is None or row['name'] not in exclude:
                columns.append(row['name'])

        return columns
