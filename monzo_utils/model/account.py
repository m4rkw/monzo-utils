import sys
from monzo_utils.model.base import BaseModel
from monzo_utils.model.pot import Pot
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.db import DB

class Account(BaseModel):

    DISPLAY_KEYS = ['name','sortcode','account_no','balance','available']


    def transactions(self, orderby='timestamp', orderdir='asc', limit=None):
        return super().related_query('Transaction', 'account_id', self.id, orderby, orderdir, limit)


    def pots(self, orderby='name', orderdir='asc', limit=None):
        return self.related('Pot', 'account_id', self.id, orderby, orderdir, limit, deleted=0)


    def get_pot(self, name):
        return Pot.one(account_id=self.id, name=name, deleted=0)


    @property
    def __dict__(self):
        attributes = {'attributes': self.attributes}

        for pot in self.pots(orderby='name'):
            attributes['attributes'][pot.name] = pot.balance

        return attributes


    @property
    def keys(self):
        keys = []

        for key in self.DISPLAY_KEYS.copy():
            if '-t' in sys.argv and ((key == 'sortcode' and self.sortcode is None) or \
                (key == 'account_no' and self.account_no is None)):
                continue

            keys.append(key)

        for pot in self.pots(orderby='name'):
            if pot.name not in keys:
                keys.append(pot.name)

        return keys


    def last_salary_transaction(self, description, salary_minimum, salary_payment_day):
        if type(description) == list:
            salary_desc = description
        else:
            salary_desc = [description]

        filter_expression = 'declined = :declined AND money_in >= :salary_minimum AND ('
        attr_names = {
            '#description': 'description'
        }
        attr_values = {
            ':declined': {'N': '0'},
            ':salary_minimum': {'N': str(salary_minimum)}
        }

        for i in range(0, len(salary_desc)):
            if i >0:
                filter_expression += ' OR '

            filter_expression += f'contains(#description, :salarydesc{i})'
            attr_values[f':salarydesc{i}'] = {'S': salary_desc[i]}

        filter_expression += ' )'

        for transaction in Transaction().find({'account_id': self.id}, filter_expression=filter_expression, attr_names=attr_names, attr_values=attr_values, orderby='created_at', orderdir='desc'):
            day = transaction.date.day

            if day >= salary_payment_day - 4 and day <= salary_payment_day:
                return transaction

        return None
