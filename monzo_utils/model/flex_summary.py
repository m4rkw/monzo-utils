import datetime
import math
from monzo_utils.model.payment import Payment
from monzo_utils.model.account import Account
from monzo_utils.model.transaction import Transaction
from monzo_utils.lib.transactions_seen import TransactionsSeen

class FlexSummary(Payment):

    def __init__(self, config, account, total, total_next_month, remaining, last_salary_date, next_salary_date, following_salary_date):
        self.config = config
        self.account = account
        self.payment_config = {
            'name': 'Flex Summary',
            'desc': 'Flex'
        }
        self.flex_total = total
        self.flex_total_next_month = total_next_month
        self.flex_remaining = remaining
        self.last_salary_date = last_salary_date
        self.next_salary_date = next_salary_date
        self.following_salary_date = following_salary_date

        self.cache = {}


    @property
    def name(self):
        return 'Flex Payment'


    @property
    def display_amount(self):
        if self.last_payment:
            return self.last_payment.money_in

        return self.flex_total


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

        account = Account.one("select * from account where name = %s", [self.config['flex_account']])

        transactions_by_diff = {}

        for transaction in Transaction.find("select * from transaction where account_id = %s and declined = %s and description = %s and `date` > %s order by created_at asc", [
                account.id,
                0,
                'Flex',
                self.last_salary_date
            ]):
            if transaction.settled.day == 16:
                diff = int(abs(self.flex_total - transaction.money_in) * 100)

                if diff not in transactions_by_diff:
                    transactions_by_diff[diff] = []

                transactions_by_diff[diff].append(transaction)

        if len(transactions_by_diff) >0:
            transaction = transactions_by_diff[sorted(transactions_by_diff.keys())[0]][0]
        else:
            transaction = None

        self.cache['last_payment'] = transaction

        return transaction


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
