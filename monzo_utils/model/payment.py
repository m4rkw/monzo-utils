import re
import datetime
from monzo_utils.lib.config import Config
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.transactions import Transactions

class Payment:

    transaction_type = 'money_out'
    always_fixed = False

    def __init__(self, config, payment_list_config, payment_config, last_salary_date, next_salary_date, following_salary_date):
        self.config = config
        self.payment_list_config = payment_list_config
        self.payment_config = payment_config
        self.last_salary_date = last_salary_date
        self.next_salary_date = next_salary_date
        self.following_salary_date = following_salary_date

        self.today = datetime.datetime.now()

        self.cache = {}


    def display(self):
        if self.num_paid is not None:
            suffix = '%d/%d' % (
                self.num_paid,
                self.num_total
            )
        else:
            suffix = ''

        if self.remaining is not None:
            remaining = '£%.2f' % (self.remaining)
        else:
            remaining = ''

        print("%s: %s %s %s %s %s %s %s" % (
            self.status.rjust(7),
            self.payment_type.ljust(15),
            self.name.ljust(25),
            suffix.ljust(4),
            ('£%.2f' % (self.display_amount)).ljust(8),
            remaining.ljust(8),
            self.last_date.strftime('%Y-%m-%d').ljust(12) if self.last_date else ''.ljust(12),
            self.due_date.strftime('%Y-%m-%d').ljust(10) if self.due_date else ''
        ))


    @property
    def name(self):
        return self.payment_config['name']


    @property
    def status(self):
        if 'start_date' in self.payment_config and self.payment_config['start_date'] >= self.next_salary_date:
            return 'SKIPPED'

        if 'yearly_month' in self.payment_config:
            if self.yearly_payment_due_this_month(self.payment_config, self.last_salary_date) is False:
                return 'SKIPPED'

        if 'renew_date' in self.payment_config and self.payment_config['renew_date'] >= self.next_salary_date:
            return 'SKIPPED'

        if 'exclude_months' in self.payment_config and self.today.month in self.payment_config['exclude_months']:
            return 'SKIPPED'

        if self.last_date and self.last_date >= self.last_salary_date:
            return 'PAID'

        if self.due_date and self.due_date >= self.next_salary_date:
            return 'SKIPPED'

        return 'DUE'


    @property
    def payment_type(self):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', type(self).__name__).replace('_',' ')


    @property
    def num_paid(self):
        return None


    @property
    def num_total(self):
        if 'months' in self.payment_config:
            return self.payment_config['months']

        return None


    @property
    def remaining(self):
        pass


    @property
    def display_amount(self):
        if 'last_amount_overrides' in Config().keys and \
            self.payment_config['name'] in Config().last_amount_overrides and \
            self.last_salary_amount in Config().last_amount_overrides[self.payment_config['name']]:

            amount = Config().last_amount_overrides[self.payment_config['name']][self.last_salary_amount]
        elif self.last_payment:
            amount = float(getattr(self.last_payment, self.transaction_type))
        else:
            amount = self.payment_config['amount']

        if self.transaction_type == 'money_in':
            return 0 - amount

        return amount


    @property
    def last_date(self):
        if 'last_date' in self.cache:
            return self.cache['last_date']

        if 'last_date_overrides' in Config().keys and \
            self.payment_config['name'] in Config().last_date_overrides and \
            self.last_salary_date in Config().last_date_overrides[self.payment_config['name']]:

            self.cache['last_date'] = Config().last_date_overrides[self.payment_config['name']][self.last_salary_date]

            return self.cache['last_date']

        if 'desc' not in self.payment_config:
            self.cache['last_date'] = None

            return self.cache['last_date']

        if self.last_payment:
            self.cache['last_date'] = self.last_payment.date
        else:
            if self.older_last_payment is not None:
                self.cache['last_date'] = self.older_last_payment.date
            else:
                self.cache['last_date'] = None

        return self.cache['last_date']


    @property
    def last_payment(self):
        if 'last_payment' in self.cache:
            return self.cache['last_payment']

        if 'desc' not in self.payment_config:
            self.payment_config['desc'] = type(self).__name__

        where=[{'clause': self.transaction_type + ' > %s', 'params': [0]}]

        if 'start_date' in self.payment_config:
            where.append({
                'clause': '`date` >= %s',
                'params': [self.payment_config['start_date']]
            })

        if self.always_fixed or 'fixed' in self.payment_config and self.payment_config['fixed']:
            method_name = f"find_all_by_declined_and_{self.transaction_type}_and_description"

            transactions = getattr(Transaction(), method_name)(
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

                self.cache['last_payment'] = transaction

                return self.cache['last_payment']

        self.cache['last_payment'] = None

        return self.cache['last_payment']


    # older last payment, may be before start_date
    @property
    def older_last_payment(self):
        if 'older_last_payment' in self.cache:
            return self.cache['older_last_payment']

        if 'desc' not in self.payment_config:
            self.payment_config['desc'] = type(self).__name__

        where=[{'clause': self.transaction_type + ' > %s', 'params': [0]}]

        if self.always_fixed or 'fixed' in self.payment_config and self.payment_config['fixed']:
            method_name = f"find_all_by_declined_and_{self.transaction_type}_and_description"

            transactions = getattr(Transaction(), method_name)(
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


    @property
    def due_date(self):
        if 'yearly_month' in self.payment_config:
            day = self.today + datetime.timedelta(days=1)

            while day.month != self.payment_config['yearly_month'] or day.day != self.payment_config['yearly_day']:
                day += datetime.timedelta(days=1)

            return datetime.date(day.year, day.month, day.day)

        if 'renew_date' in self.payment_config:
            return self.payment_config['renew_date']

        if not self.last_date:
            if 'start_date' in self.payment_config:
                return self.payment_config['start_date']

            return None

        if self.last_date.month == 12:
            due_date = datetime.date(self.last_date.year+1, 1, self.last_date.day)
        else:
            due_date = datetime.date(self.last_date.year, self.last_date.month+1, self.last_date.day)

        if 'start_date' in self.payment_config and due_date < self.payment_config['start_date']:
            return self.payment_config['start_date']

        return due_date


    @property
    def due_next_month(self):
        if 'renew_date' in self.payment_config:
            return self.payment_config['renew_date'] < self.following_salary_date

        if 'start_date' in self.payment_config and self.payment_config['start_date'] >= self.following_salary_date:
            return False

        if self.due_date is None:
            return True

        return self.due_date < self.following_salary_date


    def yearly_payment_due_this_month(self, payment, last_salary_date):
        date_from = last_salary_date.strftime('%Y-%m-%d')
        date = last_salary_date

        while date.day <= 15:
            date += datetime.timedelta(days=1)

        while date.day != 15:
            date += datetime.timedelta(days=1)

        date_to = date.strftime('%Y-%m-%d')

        due_date = str(last_salary_date.year) + '-' + (str(payment['yearly_month']).rjust(2,'0')) + '-' + (str(payment['yearly_day']).rjust(2,'0'))

        return due_date >= date_from and due_date <= date_to
