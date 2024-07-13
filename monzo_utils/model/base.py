import re
import sys
import json
import importlib
import datetime
import decimal
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config

class BaseModel:

    primary_key = 'id'

    @classmethod
    def one(cls, **kwargs):
        table = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

        row = DB().one(table, **kwargs)

        if row:
            table = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

            return getattr(importlib.import_module(f"monzo_utils.model.{table}"), cls.__name__)(row)

        return None


    @classmethod
    def find(cls, param1=None, param2=None, param3=None, limit=None, orderby=None, orderdir=None, filter_expression=None, attr_names=None, attr_values=None, key_condition_expression=None):
        table = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

        if Config().db['driver'] == 'dynamodb':
            data = DB().query('select', table, param1, limit=limit, orderby=orderby, orderdir=orderdir, filter_expression=filter_expression, attr_names=attr_names, attr_values=attr_values, key_condition_expression=key_condition_expression)
        else:
            data = DB().query(param1, param2, param3, limit=limit, orderby=orderby, orderdir=orderdir)

        results = []

        for row in data:
            results.append(getattr(importlib.import_module(f"monzo_utils.model.{table}"), cls.__name__)(row))

        return results


    @classmethod
    def search(cls, limit=None, orderby=None, orderdir=None, filter_expression=None, attr_names=None, attr_values=None):
        table = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

        if Config().db['driver'] == 'dynamodb':
            data = DB().search(table, limit=limit, orderby=orderby, orderdir=orderdir, filter_expression=filter_expression, attr_names=attr_names, attr_values=attr_values)
        else:
            data = DB().query(param1, param2, param3, limit=limit, orderby=orderby, orderdir=orderdir)

        results = []

        for row in data:
            results.append(getattr(importlib.import_module(f"monzo_utils.model.{table}"), cls.__name__)(row))

        return results



    def __init__(self, attributes=None):
        self.attributes = {}
        self.state = {
            'modified': False
        }
        self.factory_query = False
        self.table = re.sub(r'(?<!^)(?=[A-Z])', '_', self.__class__.__name__).lower()

        if type(attributes) == dict:
            self.attributes = attributes


    def __getattr__(self, name):
        try:
            return self.state[name]
        except:
            pass

        try:
            return self.attributes[name]
        except:
            pass

        if name == 'id':
            return None

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


    def __bool__(self):
        return 'id' in self.__dict__.get('attributes', {})


    def __setattr__(self, name, value):
        if name not in ['table','state','attributes','factory_query']:
            self.attributes[name] = value
        else:
            super().__setattr__(name, value)


    def __delattr__(self, name):
        try:
            self.attributes.pop(name)
        except KeyError:
            pass


    def __str__(self):
        for_display = {}

        for key in self.attributes:
            if type(self.attributes[key]) == datetime.date:
                for_display[key] = self.attributes[key].strftime('%Y-%m-%d')
            elif type(self.attributes[key]) == datetime.datetime:
                for_display[key] = self.attributes[key].strftime('%Y-%m-%d %H:%M:%S')
            elif type(self.attributes[key]) == decimal.Decimal:
                for_display[key] = float(self.attributes[key])
            else:
                for_display[key] = self.attributes[key]

        return json.dumps(for_display,indent=4)


    def related(self, model, key_field, parent_id, orderby, orderdir, limit, deleted=None):
        table = model.lower()

        if Config().db['driver'] == 'dynamodb':
            related = []

            for row in DB().query('select', table, {key_field: parent_id}, orderby=orderby, orderdir=orderdir, deleted=deleted, limit=limit):
                related.append(getattr(importlib.import_module(f"monzo_utils.model.{table}"), model)(row))

        else:
            sql = f"select * from `{table}` where {key_field} = %s"
            params = [parent_id]

            if deleted is not None:
                sql += f" and deleted = %s"
                params.append(deleted)

            sql += f" order by {orderby} {orderdir}"

            if limit:
                sql += " limit %s"
                params.append(limit)

            related = []
            for row in DB().query(sql, params):
                related.append(getattr(importlib.import_module(f"monzo_utils.model.{table}"), model)(row))

        return related


    def related_query(self, model, key_field, parent_id, orderby, orderdir, limit, deleted=None):
        table = model.lower()

        related = []

        for row in DB().query('find', table, {key_field: parent_id}, orderby=orderby, orderdir=orderdir, deleted=deleted, limit=limit):
            related.append(getattr(importlib.import_module(f"monzo_utils.model.{table}"), model)(row))

        return related


    def update(self, attributes):
        for key in attributes:
            if key not in self.attributes or self.attributes[key] != attributes[key]:
#                if key in self.attributes:
#                    print(f"{self.table} {key} [{self.attributes[key]}] {type(self.attributes[key])} => [{attributes[key]}] {type(attributes[key])}")
#                else:
#                    print(f"{self.table} {key} [NONE] => [{attributes[key]}] {type(attributes[key])}")

                self.attributes[key] = attributes[key]
                self.state['modified'] = True


    def save(self):
        if self.state['modified'] is False:
            return

        if self.id:
            DB().update(self.table, self.id, self.attributes)
        else:
            self.id = DB().create(self.table, self.attributes.copy())


    def delete(self):
        DB().delete(self.table, self.primary_key, getattr(self, self.primary_key))


    def factory(self):
        if self.factory_query is False:
            DB().find(self.table)
            self.factory_query = True


    def select(self, select):
        self.factory()

        DB().select(select)

        return self


    def join(self, join_table):
        if join_table not in self.RELATIONSHIPS:
            raise Exception(f"no relationship defined between {self.table} and {join_table}")

        self.factory()

        DB().join(join_table, self.RELATIONSHIPS[join_table][0], self.RELATIONSHIPS[join_table][1])

        return self


    def leftJoin(self, join_table, where=None):
        if join_table not in self.RELATIONSHIPS:
            raise Exception(f"no relationship defined between {self.table} and {join_table}")

        self.factory()

        DB().leftJoin(join_table, self.RELATIONSHIPS[join_table][0], self.RELATIONSHIPS[join_table][1], where)

        return self


    def where(self, clause, params):
        self.factory()

        DB().where(clause, params)

        return self


    def andWhere(self, clause, params):
        self.factory()

        DB().andWhere(clause, params)

        return self


    def groupBy(self, group_by):
        self.factory()

        DB().groupBy(group_by)

        return self


    def orderBy(self, orderby, orderdir):
        self.factory()

        DB().orderBy(orderby, orderdir)

        return self


    def getall(self):
        self.factory()

        return DB().getall()        


    def getone(self):
        self.factory()

        return DB().getone()
