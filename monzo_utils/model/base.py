import re
import sys
import json
import importlib
import datetime
import decimal
from monzo_utils.lib.db import DB

class BaseModel:

    def __init__(self, data=None, params=None):
        self.attributes = {}
        self.table = re.sub(r'(?<!^)(?=[A-Z])', '_', type(self).__name__).lower()
        self.factory_query = False

        if data:
            if type(data) == dict:
                self.attributes = data
            else:
                row = DB().one(data, params)

                if row:
                    self.attributes = row


    def find(self, sql, params):
        rows = DB().query(sql, params)

        data = []

        for row in rows:
            data.append(getattr(importlib.import_module(f"monzo_utils.model.{self.table}"), self.__class__.__name__)(row))

        return data


    def __getattr__(self, name):
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
        if name not in ['table','attributes','factory_query']:
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


    def update(self, attributes):
        self.attributes.update(attributes)


    def save(self):
        if self.id:
            DB().update(self.table, self.id, self.attributes)
        else:
            self.id = DB().create(self.table, self.attributes.copy())


    def delete(self):
        if self.id is None:
            raise Exception("Unable to delete record with null id")

        DB().query(f"delete from {self.table} where id = %s", [self.id])


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
