import datetime
import math
from monzo_utils.model.payment import Payment
from monzo_utils.model.account import Account
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.transactions_seen import TransactionsSeen

class Flex(Payment):

    def __init__(self, config, account, payment_list_config, payment_config, last_salary_date, next_salary_date, following_salary_date):
        payment_config['desc'] = 'Flex'

        super().__init__(config, account, payment_list_config, payment_config, last_salary_date, next_salary_date, following_salary_date)


    @property
    def name(self):
        return '- ' + self.payment_config['name']


    @property
    def due_date(self):
        date_due = self.today + datetime.timedelta(days=1)

        if 'start_date' in self.payment_config:
            date_due = self.payment_config['start_date']

        for i in range(0, self.payment_config['months']):
            while date_due.day != self.config['flex_payment_date']:
                date_due += datetime.timedelta(days=1)

            if datetime.date(date_due.year, date_due.month, date_due.day) > datetime.date(self.today.year, self.today.month, self.today.day):
                return datetime.date(date_due.year, date_due.month, date_due.day)

            date_due += datetime.timedelta(days=1)

        return None


    @property
    def num_paid(self):
        date = self.payment_config['start_date']
        num_paid = 0

        for i in range(0, self.payment_config['months']):
            while date.day != self.config['flex_payment_date']:
                date += datetime.timedelta(days=1)

            if date <= datetime.date(self.today.year, self.today.month, self.today.day):
                num_paid += 1

            date += datetime.timedelta(days=1)

        return num_paid


    @property
    def display_amount(self):
        date = self.payment_config['start_date']

        total_paid = 0

        for i in range(0, self.payment_config['months']):
            amount = int(math.ceil(self.payment_config['amount'] / self.payment_config['months']))

            if total_paid + amount > self.payment_config['amount']:
                amount = self.payment_config['amount'] - total_paid

            while date.day != self.config['flex_payment_date']:
                date += datetime.timedelta(days=1)

            if date <= datetime.date(self.today.year, self.today.month, self.today.day):
                total_paid += amount
            else:
                break

            date += datetime.timedelta(days=1)

        return amount


    @property
    def remaining(self):
        date = self.payment_config['start_date']

        total_paid = 0

        for i in range(0, self.payment_config['months']):
            amount = int(math.ceil(self.payment_config['amount'] / self.payment_config['months']))

            if total_paid + amount > self.payment_config['amount']:
                amount = self.payment_config['amount'] - total_paid

            while date.day != self.config['flex_payment_date']:
                date += datetime.timedelta(days=1)

            if date <= datetime.date(self.today.year, self.today.month, self.today.day):
                total_paid += amount
            else:
                break

            date += datetime.timedelta(days=1)

        return self.payment_config['amount'] - total_paid


    def amount_for_period(self, salary_from_date, salary_to_date):
        total = self.payment_config['amount']

        date = self.payment_config['start_date']

        if date >= salary_to_date:
            return 0

        paid = 0
        found = False

        for i in range(0, self.payment_config['months']):
            while date.day != self.config['flex_payment_date']:
                date += datetime.timedelta(days=1)

            amount = int(math.ceil(self.payment_config['amount'] / self.payment_config['months']))

            if paid + amount > total:
                amount = total - paid

            paid += amount

            if salary_from_date < date:
                found = True
                break

            date += datetime.timedelta(days=1)

        if not found:
            return 0

        return amount


    # older last payment, may be before start_date
    @property
    def older_last_payment(self):
        if 'older_last_payment' in self.cache:
            return self.cache['older_last_payment']

        where, params = self.get_transaction_where_condition()

        sql = "select * from transaction"

        if 'metadata' in self.payment_config:
            for i in range(0, len(self.payment_config['metadata'])):
                sql += " join transaction_metadata meta%d on transaction.id = meta%d.transaction_id" % (i+1, i+1)

        transactions = Transaction.find(
            f"{sql} where {where} order by created_at desc",
            params
        )

        for transaction in transactions:
            if transaction.date.day != self.config['flex_payment_date']:
                continue

            if transaction.id not in TransactionsSeen().seen:
                TransactionsSeen().seen[transaction.id] = 1

                self.cache['older_last_payment'] = transaction

                return self.cache['older_last_payment']

        self.cache['older_last_payment'] = None

        return self.cache['older_last_payment']
