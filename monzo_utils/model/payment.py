import re
import datetime
from monzo_utils.lib.config import Config
from monzo_utils.model.transaction import Transaction
from monzo_utils.model.provider import Provider
from monzo_utils.model.account import Account
from monzo_utils.lib.transactions_seen import TransactionsSeen
from currency_converter import CurrencyConverter

class Payment:

    transaction_type = 'money_out'
    always_fixed = False

    def __init__(self, config, account, payment_list_config, payment_config, last_salary_date, next_salary_date, following_salary_date):
        self.config = config
        self.account = account
        self.payment_list_config = payment_list_config
        self.payment_config = payment_config
        self.last_salary_date = last_salary_date
        self.next_salary_date = next_salary_date
        self.following_salary_date = following_salary_date

        self.today = datetime.datetime.now()

        self.cache = {}


    def data(self, abbreviate=False):
        if self.num_paid is not None:
            suffix = '%d/%d' % (
                self.num_paid,
                self.num_total
            )
        else:
            suffix = ''

        if self.remaining is not None:
            remaining = self.remaining
        else:
            remaining = None

        return {
            'status': self.status,
            'payment_type': self.payment_type if abbreviate is False else self.abbreviate(self.payment_type),
            'name': self.name,
            'suffix': suffix,
            'amount': self.display_amount,
            'remaining': remaining,
            'last_date': self.short_date(self.last_date) if abbreviate else self.last_date,
            'due_date': self.short_date(self.due_date) if abbreviate else self.due_date
        }


    def abbreviate(self, string):
        abbreviated = ''

        for i in range(0, len(string)):
            if string[i].isupper():
                abbreviated += string[i]

        return abbreviated


    def short_date(self, date):
        if not date:
            return None

        return date.strftime('%d/%m/%y')


    def display_output(self):
        data = self.data()

        if self.__class__.__name__ == 'Flex':
            amount = ('£%.2f' % (data['amount'])).ljust(19)
        elif self.__class__.__name__ == 'FlexSummary':
            if ('%.2f' % (data['amount'])) != ('%.2f' % (self.flex_total_next_month)):
                amount = ('£%.2f' % (data['amount'])).ljust(9) + \
                    ('->£%.2f' % (self.flex_total_next_month)).ljust(10)
            else:
                amount = ('£%.2f' % (data['amount'])).ljust(19)
        else:
            if data['status'] != 'DUE' and self.last_payment and self.last_payment.money_out:
                if 'last_amount_overrides' in self.config and \
                    self.payment_config['name'] in self.config['last_amount_overrides'] and \
                    self.last_salary_date in self.config['last_amount_overrides'][self.payment_config['name']]:

                    last_amount = self.config['last_amount_overrides'][self.payment_config['name']][self.last_salary_date]
                else:
                    last_amount = self.last_payment.money_out
            else:
                last_amount = data['amount']

            if last_amount == None:
                amount = ''
            elif ('%.2f' % (last_amount)) == ('%.2f' % (self.next_month_amount)):
                amount = ('£%.2f' % (last_amount)).ljust(19)
            else:
                amount = ('£%.2f' % (last_amount)).ljust(9) + \
                    ('->£%.2f' % (self.next_month_amount)).ljust(10)

        return {
            'Status': data['status'] + ':',
            'Type': data['payment_type'],
            'Name': data['name'],
            'Count': data['suffix'],
            'Amount': amount,
            'Left': '£%.2f' % (data['remaining']) if data['remaining'] else '',
            'Last date': data['last_date'].strftime('%Y-%m-%d') if data['last_date'] else '',
            'Due date': data['due_date'].strftime('%Y-%m-%d') if data['due_date'] else ''
        }


    @property
    def name(self):
        return self.payment_config['name']


    @property
    def status(self):
        if 'start_date' in self.payment_config and self.payment_config['start_date'] >= self.next_salary_date:
            return 'SKIPPED'

        if 'yearly_month' in self.payment_config:
            if self.yearly_payment_due_this_month() is False:
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
        if 'display_amount' in self.cache:
            return self.cache['display_amount']

        if self.status == 'DUE' and 'reserve_amount' in self.payment_config:
            self.cache['display_amount'] = self.payment_config['reserve_amount']

            return self.payment_config['reserve_amount']

        today = datetime.datetime.now()
        today = datetime.date(today.year, today.month, today.day)

        if 'last_amount_overrides' in Config().keys and \
            self.payment_config['name'] in Config().last_amount_overrides and \
            self.last_salary_date in Config().last_amount_overrides[self.payment_config['name']]:

            amount = Config().last_amount_overrides[self.payment_config['name']][self.last_salary_date]

            self.cache['display_amount'] = amount

            return amount

        elif 'renewal' in self.payment_config and ((self.payment_config['renewal']['date'] < self.next_salary_date and self.payment_config['renewal']['date'] > self.last_salary_date) or self.status == 'PAID'):
            if 'first_payment' in self.payment_config['renewal'] and self.payment_config['renewal']['date'] >= self.last_salary_date:
                amount = self.payment_config['renewal']['first_payment']
            else:
                amount = self.payment_config['renewal']['amount']

        elif self.last_payment:
            amount = float(getattr(self.last_payment, self.transaction_type))

            if self.transaction_type == 'money_in':
                return 0 - amount

            self.cache['display_amount'] = amount

            return amount
        else:
            amount = self.payment_config['amount']

        if self.transaction_type == 'money_in':
            return 0 - amount

        if 'currency' in self.payment_config and self.payment_config['currency'] != 'GBP':
            amount = self.convert_currency(amount, self.payment_config['currency'])

        self.cache['display_amount'] = amount

        return amount


    def convert_currency(self, amount, currency):
        c = CurrencyConverter()

        return c.convert(amount, currency, 'GBP')


    @property
    def next_month_amount(self):
        if 'renewal' not in self.payment_config:
            return self.display_amount

        if 'first_payment' in self.payment_config['renewal'] and self.payment_config['renewal']['date'] >= self.next_salary_date:
            amount = self.payment_config['renewal']['first_payment']
        else:
            amount = self.payment_config['renewal']['amount']

        if 'currency' in self.payment_config and self.payment_config['currency'] != 'GBP':
            amount = self.convert_currency(amount, self.payment_config['currency'])

        return amount


    @property
    def last_date(self):
        if 'last_date' in self.cache:
            return self.cache['last_date']

        if 'last_date_overrides' in self.config and \
            self.payment_config['name'] in self.config['last_date_overrides'] and \
            self.last_salary_date in self.config['last_date_overrides'][self.payment_config['name']]:

            self.cache['last_date'] = self.config['last_date_overrides'][self.payment_config['name']][self.last_salary_date]

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


    def get_transaction_where_condition(self, amounts=True):
        if 'desc' not in self.payment_config:
            self.payment_config['desc'] = type(self).__name__

        where = "( account_id = %s"
        params = [self.account.id]

        if 'other_accounts' in self.payment_config:
            for other_account in self.payment_config['other_accounts']:
                provider = Provider.one("select * from provider where name = %s", [other_account['provider']])
                account = Account.one("select * from account where provider_id = %s and name = %s", [provider.id, other_account['name']])

                where += " or account_id = %s"
                params.append(account.id)

        where += f") and {self.transaction_type} > %s and declined = %s"
        params += [0, 0]

        if type(self.payment_config['desc']) == list:
            desc_list = self.payment_config['desc']
        else:
            desc_list = [self.payment_config['desc']]

        where += " and ( "

        for i in range(0, len(desc_list)):
            if i >0:
                where += " or "
            where += " description like %s "
            params.append('%' + desc_list[i] + '%')

        if 'metadata' in self.payment_config:
            where += " or ("

            keys = list(sorted(list(self.payment_config['metadata'].keys())))

            for i in range(0, len(keys)):
                if i >0:
                    where += " and "

                where += " meta1.key = %s and meta1.value like %s"
                params.append(keys[i])
                params.append(self.payment_config['metadata'][keys[i]])

            where += " ) "

        where += ")"

        if 'start_date' in self.payment_config:
            where += f" and `date` >= %s"
            params.append(self.payment_config['start_date'].strftime('%Y-%m-%d'))

        if amounts is True and (self.always_fixed or ('fixed' in self.payment_config and self.payment_config['fixed'])):
            where += f" and {self.transaction_type} = %s"
            params.append(self.payment_config['amount'])
        elif amounts is not False and amounts is not True and amounts is not None:
            if type(amounts) != list:
                amounts = [amounts]

            where += ' and ('

            for i in range(0, len(amounts)):
                if i >0:
                    where += ' or '
                where += f' {self.transaction_type} = %s'
                params.append(amounts[i])

            where += ')'

        return where, params


    @property
    def last_payment(self):
        if 'last_payment' in self.cache:
            return self.cache['last_payment']

        where, params = self.get_transaction_where_condition()

        sql = "select * from transaction"

        if 'metadata' in self.payment_config:
            for i in range(0, len(self.payment_config['metadata'])):
                sql += " join transaction_metadata meta%d on transaction.id = meta%d.transaction_id" % (i+1, i+1)

        transactions = Transaction.find(f"{sql} where {where} order by created_at desc", params)

        for transaction in transactions:
            if 'start_date' in self.payment_config and transaction.date < self.payment_config['start_date']:
                continue

            if transaction.id not in TransactionsSeen().seen:
                TransactionsSeen().seen[transaction.id] = 1

                self.cache['last_payment'] = transaction

                return self.cache['last_payment']

        self.cache['last_payment'] = None

        return self.cache['last_payment']


    # older last payment, may be before start_date
    @property
    def older_last_payment(self):
        if 'older_last_payment' in self.cache:
            return self.cache['older_last_payment']

        where, params = self.get_transaction_where_condition()

        transactions = Transaction.find(
            f"select * from transaction where {where} order by created_at desc",
            params
        )

        for transaction in transactions:
            if transaction.id not in TransactionsSeen().seen:
                TransactionsSeen().seen[transaction.id] = 1

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

            due_date = datetime.date(day.year, day.month, day.day)

            if self.last_date:
                days_since_last_payment = (due_date - self.last_date).total_seconds() / 86400

                if days_since_last_payment < 90:
                    due_date = datetime.date(due_date.year + 1, self.payment_config['yearly_month'], self.payment_config['yearly_day'])

            return due_date

        if 'renew_date' in self.payment_config:
            return self.payment_config['renew_date']

        if not self.last_date:
            if 'start_date' in self.payment_config:
                return self.payment_config['start_date']

            return None

        if self.last_date.month == 12:
            due_date = datetime.date(self.last_date.year+1, 1, self.last_date.day)
        else:
            day = self.last_date.day

            while 1:
                try:
                    due_date = datetime.date(self.last_date.year, self.last_date.month+1, day)
                    break
                except:
                    day -= 1

        if 'start_date' in self.payment_config and due_date < self.payment_config['start_date']:
            return self.payment_config['start_date']

        if 'yearly_month' not in self.payment_config:
            if 'exclude_months' in self.payment_config:
                while due_date.month in self.payment_config['exclude_months']:
                    if due_date.month == 12:
                        due_date = datetime.date(due_date.year+1, 1, due_date.day)
                    else:
                        due_date = datetime.date(due_date.year, due_date.month+1, due_date.day)

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


    def yearly_payment_due_this_month(self):
        date_from = self.last_salary_date.strftime('%Y-%m-%d')
        date = self.last_salary_date

        while date.day <= self.config['salary_payment_day']:
            date += datetime.timedelta(days=1)

        while date.day != self.config['salary_payment_day']:
            date += datetime.timedelta(days=1)

        date_to = date.strftime('%Y-%m-%d')

        due_date = str(self.last_salary_date.year) + '-' + (str(self.payment_config['yearly_month']).rjust(2,'0')) + '-' + (str(self.payment_config['yearly_day']).rjust(2,'0'))

        return due_date >= date_from and due_date <= date_to
