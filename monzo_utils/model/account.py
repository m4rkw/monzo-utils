import sys
from monzo_utils.model.base import BaseModel
from monzo_utils.model.pot import Pot
from monzo_utils.lib.db import DB

class Account(BaseModel):

    DISPLAY_KEYS = ['name','sortcode','account_no','balance','available']


    def transactions(self, orderby='created_at', orderdir='asc', limit=None):
        return super().related('Transaction', 'account_id', self.id, orderby, orderdir, limit)


    def pots(self, orderby='name', orderdir='asc', limit=None):
        return self.related('Pot', 'account_id', self.id, orderby, orderdir, limit, deleted=0)


    def get_pot(self, name):
        return Pot("select * from pot where account_id = %s and name = %s and deleted = %s", [self.id, name, 0])


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

        where = f"account_id = %s and declined = %s and money_in >= %s and ("
        params = [self.id, 0, salary_minimum]

        for i in range(0, len(salary_desc)):
            if i >0:
                where += ' or '
            where += " description like %s"
            params.append('%' + salary_desc[i] + '%')

        where += ")"

        for row in DB().query(f"select * from transaction where {where} order by created_at desc", params):
            day = row['date'].day

            if row['date'].day >= salary_payment_day - 4 and row['date'].day <= salary_payment_day:
                return row

        return None
