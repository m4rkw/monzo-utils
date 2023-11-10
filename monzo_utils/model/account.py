import sys
from monzo_utils.model.base import BaseModel
from monzo_utils.lib.db import DB

class Account(BaseModel):

    DISPLAY_KEYS = ['name','sortcode','account_no','balance','available']


    def __init__(self, attrs={}):
        super().__init__(attrs)


    def transactions(self, orderby='created_at', orderdir='asc', limit=None):
        return super().related('Transaction', 'account_id', self.id, orderby, orderdir, limit)


    def pots(self, orderby='name', orderdir='asc', limit=None):
        return super().related('Pot', 'account_id', self.id, orderby, orderdir, limit, deleted=0)


    @property
    def __dict__(self):
        attrs = {'attrs': self.attrs}

        for pot in self.pots(orderby='name'):
            attrs['attrs'][pot.name] = pot.balance

        return attrs


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


    def last_salary_transaction(self, description, payment_day, salary_minimum):
        return DB().find_transaction_by_account_id_and_declined_and_description(
            self.id,
            0,
            description,
            orderby='created_at',
            orderdir='desc',
            limit=1,
            search=['description'],
            where=[{
                'clause': 'money_in >= %s',
                'params': [salary_minimum]
            }]
        )
