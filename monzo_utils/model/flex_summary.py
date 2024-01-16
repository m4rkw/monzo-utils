import datetime
import math
from monzo_utils.model.payment import Payment
from monzo_utils.model.account import Account
from monzo_utils.model.transaction import Transaction

class FlexSummary(Payment):

    def __init__(self, config, total, total_next_month, remaining, last_salary_date):
        self.config = config
        self.payment_config = {}
        self.flex_total = total
        self.flex_total_next_month = total_next_month
        self.flex_remaining = remaining
        self.last_salary_date = last_salary_date

        self.cache = {}


    @property
    def status(self):
        if self.last_payment and self.last_payment.date >= self.last_salary_date:
            return 'PAID'

        return 'DUE'


    @property
    def name(self):
        return 'Flex Payment'


    @property
    def display_amount(self):
        return self.flex_total


    @property
    def last_date(self):
        if self.last_payment:
            return self.last_payment.date

        last_date = datetime.datetime.now()

        while last_date.day != self.config['flex_payment_date']:
            last_date -= datetime.timedelta(days=1)

        return last_date


    @property
    def due_date(self):
        if 'due_date' in self.cache:
            return self.cache['due_date']

        if self.last_payment:
            due_date = self.last_payment.date

            while due_date.day != self.config['flex_payment_date']:
                due_date += datetime.timedelta(days=1)

            due_date += datetime.timedelta(days=1)

            while due_date.day != self.config['flex_payment_date']:
                due_date += datetime.timedelta(days=1)

            return due_date

        date = datetime.datetime.now() + datetime.timedelta(days=1)

        while date.day != self.config['flex_payment_date']:
            date += datetime.timedelta(days=1)

        return datetime.date(date.year, date.month, date.day)


    @property
    def remaining(self):
        return self.flex_remaining


    @property
    def last_payment(self):
        if 'last_payment' in self.cache:
            return self.cache['last_payment']

        account = Account().find_by_name(self.config['flex_account'])

        where = [{'clause': 'date > %s', 'params': [self.last_salary_date]}]

        transaction = Transaction().find_by_account_id_and_declined_and_money_in_and_description(
            account.id,
            0,
            self.display_amount,
            'Flex',
            orderby='created_at',
            orderdir='asc',
            limit=1
        )

        self.cache['last_payment'] = transaction

        return transaction
