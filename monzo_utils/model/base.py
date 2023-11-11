import re
import sys
import json
import importlib
from monzo_utils.lib.db import DB

class BaseModel:

    def __init__(self, attrs=None):
        self.table = re.sub(r'(?<!^)(?=[A-Z])', '_', type(self).__name__).lower()

        if attrs:
            self.attrs = attrs
        else:
            self.attrs = {}

        if 'id' not in self.attrs:
            self.attrs['id'] = None

        self.factory_query = False


    def __getattr__(self, name):
        if name in self.attrs:
            return self.attrs[name]

        match = re.match('^find_by_(.*?)$', name)

        if match:
            method_name = f"find_{self.table}_by_{match.group(1)}"

            def find_object_by_fields(*args, **kwargs):
                record = getattr(DB(), method_name)(*args, **kwargs)

                if record:
                    return type(self)(record)

                return record

            return find_object_by_fields

        match = re.match('^find_all_by_(.*?)$', name)

        if match:
            method_name = f"find_all_{self.table}_by_{match.group(1)}"

            def find_objects_by_fields(*args, **kwargs):
                objects = []

                for record in getattr(DB(), method_name)(*args, **kwargs):
                    objects.append(type(self)(record))

                return objects

            return find_objects_by_fields

        print("DB class method missing: %s" % (name))
        sys.exit(1)


    def __setattr__(self, name, value):
        if name not in ['table','attrs']:
            self.attrs[name] = value
        else:
            super().__setattr__(name, value)


    def __delattr__(self, name):
        self.attrs.pop(name)


    def __str__(self):
        return json.dumps(self.attrs,indent=4)


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


    def update(self, attrs):
        self.attrs.update(attrs)


    def save(self):
        if self.id:
            DB().update(self.table, self.id, self.attrs)
        else:
            self.id = DB().create(self.table, self.attrs)


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
