import boto3
import sys
import os
import re
import json
import datetime

CACHE_WHOLE_TABLES = [
    'provider',
    'account',
    'pot'
]

SECONDARY_INDICES = {
    'transaction': 'AccountTimestampIndex'
}

class dynamodb:

    def __init__(self, config):
        self.config = config
        self.columns = {}
        self.connect()
        self.prefix = self.config['table_prefix']
        self.cache = {}


    def connect(self):
        self.session = boto3.Session()
        self.dbd = self.session.client('dynamodb')


    def query(self, query_type, table, expression, limit=None, orderby=None, orderdir=None, deleted=None, filter_expression=None, attr_names=None, attr_values=None, key_condition_expression=None):
        query_method = getattr(self, query_type)

        return query_method(table, expression, limit=limit, orderby=orderby, orderdir=orderdir, deleted=deleted, filter_expression=filter_expression, attr_names=attr_names, attr_values=attr_values, key_condition_expression=key_condition_expression)


    def select(self, table, expression, limit=None, orderby=None, orderdir=None, deleted=None, filter_expression=None, attr_names=None, attr_values=None, key_condition_expression=None):
        if table in CACHE_WHOLE_TABLES:
            if table not in self.cache:
                self.cache_table(table)

            return self.find_in_cache(table, expression, limit)

        if len(expression) == 1 and filter_expression is None and key_condition_expression is None:
            key = list(expression.keys())[0]

            resp = self.dbd.get_item(
                TableName=f"{self.prefix}_{table}",
                Key={
                    key: {
                        'S': expression[key]
                    }
                }
            )

            results = []

            if 'Item' in resp:
                results.append(self.to_obj(resp['Item']))

            return results

        params = {
            'TableName': f"{self.prefix}_{table}",
            'KeyConditionExpression': '',
            'ExpressionAttributeValues': {}
        }

        if table in SECONDARY_INDICES:
            params['IndexName'] = SECONDARY_INDICES[table]

        params['KeyConditionExpression'], params['ExpressionAttributeValues'] = self.parse_key_conditions(expression)

        if key_condition_expression:
            params['KeyConditionExpression'] += f" AND {key_condition_expression}"

        if filter_expression is not None:
            params['FilterExpression'] = filter_expression
        if attr_names is not None:
            params['ExpressionAttributeNames'] = attr_names
        if attr_values is not None:
            params['ExpressionAttributeValues'].update(attr_values)

        if limit:
            params['Limit'] = limit

        if orderby is not None:
            params['ScanIndexForward'] = (orderdir == 'asc')

        results = []

        while 1:
            resp = self.dbd.query(**params)

            if 'Items' in resp:
                for item in resp['Items']:
                    results.append(self.to_obj(item))

            if 'LastEvaluatedKey' not in resp:
                break

            params['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        return results


    def parse_key_conditions(self, expression):
        key_condition_expression = ''
        attribute_values = {}

        for key in expression:
            attribute_value = ':' + key

            if len(key_condition_expression) >0:
                key_condition_expression += ' AND '

            if type(expression[key]) == list:
                key_condition_expression += "("

                for i in range(0, len(expression[key])):
                    if i >0:
                        key_condition_expression += " OR "

                    key_condition_expression += f"{key} = {attribute_value}{i}"

                    prefix, value = self.value_to_dbd(expression[key][i])

                    attribute_values[f'{attribute_value}{i}'] = {prefix: value}

                key_condition_expression += ")"
            else:
                key_condition_expression += f"{key} = {attribute_value}"

                prefix, value = self.value_to_dbd(expression[key])

                attribute_values[attribute_value] = {prefix: value}

        return key_condition_expression, attribute_values


    def value_to_dbd(self, value):
        if type(value) == int:
            return 'N', str(value)
        elif type(value) == float:
            if value == int(value):
                return 'N', str(int(value))
            else:
                return 'N', '%.2f' % (value)
        elif type(value) == bytes:
            return 'B', value
        elif type(value) == bool:
            return 'BOOL', value
        elif value is None:
            return 'NULL', True
        elif type(value) == str:
            return 'S', str(value)
        elif type(value) == datetime.date:
            return 'S', value.strftime('%Y-%m-%d')
        elif type(value) == datetime.datetime:
            return 'S', value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(value)
            print(type(value))
            raise Exception(f"unhandled data type {str(type(value))}")


    def cache_table(self, table):
        resp = self.dbd.scan(
            TableName=f"{self.prefix}_{table}"
        )

        self.cache[table] = []

        for row in resp['Items']:
            self.cache[table].append(self.to_obj(row))


    def to_obj(self, item):
        obj = {}

        for key in item:
            for field_type in item[key]:
                if field_type == 'S':
                    obj[key] = item[key]['S']

                    m = re.match(r'^([\d]{4})-([\d]{2})-([\d]{2})$', obj[key])

                    if m:
                        obj[key] = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    else:
                        m = re.match(r'^([\d]{4})-([\d]{2})-([\d]{2}) ([\d]{2}):([\d]{2}):([\d]{2})$', obj[key])

                        if m:
                            obj[key] = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))

                elif field_type == 'N':
                    if '.' in item[key]['N']:
                        obj[key] = float(item[key]['N'])
                    else:
                        obj[key] = int(item[key]['N'])
                elif field_type == 'BOOL':
                    obj[key] = item[key]['BOOL']
                elif field_type == 'NULL':
                    obj[key] = None
                elif field_type == 'B':
                    obj[key] = item[key]['B']
                else:
                    raise Exception(f"unhandled field type: {field_type}")

        return obj


    def to_dbd(self, attributes):
        item = {}

        for key in attributes:
            if type(attributes[key]) == int:
                item[key] = {
                    'N': str(attributes[key])
                }
            elif type(attributes[key]) == float:
                if int(attributes[key]) == attributes[key]:
                    item[key] = {
                        'N': str(attributes[key])
                    }
                else:
                    item[key] = {
                        'N': '%.2f' % (attributes[key])
                    }
            elif type(attributes[key]) == bytes:
                item[key] = {
                    'B': attributes[key]
                }
            elif type(attributes[key]) == bool:
                item[key] = {
                    'BOOL': attributes[key]
                }
            elif attributes[key] is None:
                item[key] = {
                    'NULL': True
                }
            elif type(attributes[key]) == str:
                item[key] = {
                    'S': str(attributes[key])
                }
            elif type(attributes[key]) == datetime.date:
                item[key] = {
                    'S': attributes[key].strftime('%Y-%m-%d')
                }
            elif type(attributes[key]) == datetime.datetime:
                item[key] = {
                    'S': attributes[key].strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                print(key)
                print(attributes[key])
                print(type(attributes[key]))
                raise Exception(f"unhandled data type {str(type(attributes[key]))}")

        return item


    def find_in_cache(self, table, expression, limit):
        results = []

        for item in self.cache[table]:
            if expression is None or self.expression_matches(item, expression):
                results.append(item)

                if limit and len(results) == limit:
                    return results

        return results


    def expression_matches(self, item, expression):
        for key in expression:
            if key not in item or item[key] != expression[key]:
                return False

        return True


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

        for row in self.query("select column_name from information_schema.columns where table_schema = %s and table_name = %s", [self.config['database'], table]):
            if exclude is None or row['column_name'] not in exclude:
                columns.append(row['column_name'])

        return columns


    def put_item(self, table, data):
        resp = self.dbd.put_item(
            TableName=f"{self.prefix}_{table}",
            Item=self.to_dbd(data)
        )


    def delete(self, table, key, data):
        if type(data) == dict:
            key = self.to_dbd(data)
        else:
            key = {key: {'S': data}}

        self.dbd.delete_item(
            TableName=f"{self.prefix}_{table}",
            Key=key
        )


    def find(self, table, expression, limit=None, orderby=None, orderdir=None, deleted=None, filter_expression=None, attr_names=None, attr_values=None):
        params = {
            'TableName': f"{self.prefix}_{table}",
            'IndexName': SECONDARY_INDICES[table],
            'KeyConditionExpression': '',
            'ExpressionAttributeValues': {}
        }

        if orderby is not None:
            params['ScanIndexForward'] = (orderdir == 'asc')

        if limit is not None:
            params['Limit'] = limit

        params['KeyConditionExpression'], params['ExpressionAttributeValues'] = self.parse_key_conditions(expression)

        if filter_expression is not None:
            params['FilterExpression'] = filter_expression
        if attr_names is not None:
            params['ExpressionAttributeNames'] = attr_names
        if attr_values is not None:
            params['ExpressionAttributeValues'].update(attr_values)

        results = []

        while 1:
            resp = self.dbd.query(**params)

            if 'Items' in resp:
                for row in resp['Items']:
                    results.append(self.to_obj(row))

            if 'LastEvaluatedKey' not in resp:
                break

            params['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        return results


    def search(self, table, limit=None, orderby=None, orderdir=None, deleted=None, filter_expression=None, attr_names=None, attr_values=None):
        params = {
            'TableName': f"{self.prefix}_{table}"
        }

        if table in SECONDARY_INDICES:
            params['IndexName'] = SECONDARY_INDICES[table]

        if filter_expression is not None:
            params['FilterExpression'] = filter_expression
        if attr_names is not None:
            params['ExpressionAttributeNames'] = attr_names
        if attr_values is not None:
            if 'ExpressionAttributeValues' not in params:
                params['ExpressionAttributeValues'] = {}
            params['ExpressionAttributeValues'].update(attr_values)

        if limit:
            params['Limit'] = limit

        if orderby is not None:
            params['ScanIndexForward'] = (orderdir == 'asc')

        results = []

        while 1:
            resp = self.dbd.scan(**params)

            if 'Items' in resp:
                for item in resp['Items']:
                    results.append(self.to_obj(item))

            if 'LastEvaluatedKey' not in resp:
                break

            params['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        return results
