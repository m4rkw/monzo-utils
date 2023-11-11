import datetime
import math
from monzo_utils.model.payment import Payment
from monzo_utils.model.transaction import Transaction

class Refund(Payment):

    @property
    def status(self):
        if self.last_payment:
            return 'PAID'

        if self.due_date and self.due_date >= self.next_salary_date:
            return 'SKIPPED'

        if self.payment_config['due_after'] >= self.next_salary_date:
            return 'SKIPPED'

        return 'DUE'


    @property
    def display_amount(self):
        return 0 - super().display_amount


    @property
    def last_payment(self):
        if 'last_payment' in self.cache:
            return self.cache['last_payment']

        if 'desc' not in self.payment_config:
            self.payment_config['desc'] = type(self).__name__

        where=[{
                'clause': 'money_in> %s',
                'params': [0]
            },
            {
                'clause': '`date` >= %s',
                'params': [self.payment_config['due_after']]
            },
            {
                'clause': 'money_in = %s',
                'params': [self.payment_config['amount']]
            }
        ]

        transaction = Transaction().find_by_declined_and_description(
            0,
            self.payment_config['desc'],
            orderby='created_at',
            orderdir='desc',
            search=['description'],
            where=where
        )

        if transaction:
            self.cache['last_payment'] = transaction
        else:
            self.cache['last_payment'] = None

        return self.cache['last_payment']


    # older last payment, may be before start_date
    @property
    def older_last_payment(self):
        if 'older_last_payment' in self.cache:
            return self.cache['older_last_payment']

        if 'desc' not in self.payment_config:
            self.payment_config['desc'] = type(self).__name__

        where=[{'clause': 'money_in > %s', 'params': [0]}]

        if 'fixed' in self.payment_config and self.payment_config['fixed']:
            transactions = Transaction().find_all_by_declined_and_money_out_and_description(
                0,
                self.payment_config['amount'],
                self.payment_config['desc'],
                orderby='created_at',
                orderdir='desc',
                search=['description'],
                where=where
            )
        else:
            transactions = Transaction().find_all_by_declined_and_description(
                0,
                self.payment_config['desc'],
                orderby='created_at',
                orderdir='desc',
                search=['description'],
                where=where
            )

        for transaction in transactions:
            if transaction.id not in Transactions().seen:
                Transactions().seen[transaction.id] = 1

                self.cache['older_last_payment'] = transaction

                return self.cache['older_last_payment']

        self.cache['older_last_payment'] = None

        return self.cache['older_last_payment']
