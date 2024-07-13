from monzo_utils.lib.config import Config
from monzo_utils.model.payment import Payment
from monzo_utils.model.transaction import Transaction
from monzo_utils.model.provider import Provider
from monzo_utils.model.account import Account
from monzo_utils.model.payments import Payments

class Finance(Payment):

    @property
    def display_amount(self):
        if 'display_amount' in self.cache:
            return self.cache['display_amount']

        if 'last_amount_overrides' in self.config and \
            self.payment_config['name'] in self.config['last_amount_overrides'] and \
            self.last_salary_date in self.config['last_amount_overrides'][self.payment_config['name']]:

            self.cache['display_amount'] = self.config['last_amount_overrides'][self.payment_config['name']][self.last_salary_date]

            return self.cache['display_amount']

        if self.last_payment:
            self.cache['display_amount'] = float(self.last_payment.money_out)

            return self.cache['display_amount']

        return int(round(self.payment_config['amount'] / self.payment_config['months'], 2) * 100) / 100


    @property
    def all_finance_transactions(self):
        if 'all_finance_transactions' in self.cache:
            return self.cache['all_finance_transactions']

        total = int(self.payment_config['amount'] * 100)

        if 'round' in self.payment_config and self.payment_config['round'] == 'up':
            if total % self.payment_config['months'] != 0:
                adjusted = total

                while adjusted % self.payment_config['months'] != 0:
                    adjusted += 1

                initial_payment = adjusted / self.payment_config['months']

                final_payment = total - (initial_payment * (self.payment_config['months']-1))

                amounts = [initial_payment / 100, final_payment / 100]
            else:
                amounts = [int(self.payment_config['amount'] / self.payment_config['months'] * 100) / 100]
        else:
            amounts = [int(self.payment_config['amount'] / self.payment_config['months'] * 100) / 100]

            final_payment = round(self.payment_config['amount'] - (amounts[0] * (self.payment_config['months']-1)), 2)

            if final_payment not in amounts:
                amounts.append(final_payment)

        if final_payment not in amounts:
            amounts.append(final_payment)

        if 'single_payment' in self.payment_config and self.payment_config['single_payment']:
            filter_expression, attr_names, attr_values, key_condition_expression = self.get_transaction_where_condition(amounts=False)

            all_transactions_hash = self.hash('all_finance_transactions', filter_expression, attr_names, attr_values, key_condition_expression, self.account.id)

            all_transactions = Payments().one(key=all_transactions_hash)

            if all_transactions is not None:
                all_finance_transactions = Transaction.all(id=all_transactions.transaction_ids.split(','))

                self.cache['all_finance_transactions'] = all_finance_transactions
                return all_finance_transactions

            self.cache['all_finance_transactions'] = []

            account_ids = [self.account.id]

            if 'other_accounts' in self.payment_config:
                for other_account in self.payment_config['other_accounts']:
                    provider = Provider.one(name=other_account['provider'])
                    account = Account.one(provider_id=provider.id, name=other_account['name'])

                    account_ids.append(account.id)

            transactions = []

            for account_id in account_ids:
                transactions += Transaction.find(
                    {'account_id': account_id},
                    filter_expression=filter_expression,
                    attr_names=attr_names,
                    attr_values=attr_values,
                    orderby='created_at',
                    orderdir='asc',
                    key_condition_expression=key_condition_expression
                )

            transaction_ids = []
            for transaction in transactions:
                if 'monthly_day' in self.payment_config and transaction.date.day != self.payment_config['monthly_day']:
                    continue

                self.cache['all_finance_transactions'].append(transaction)
                transaction_ids.append(transaction.id)

            all_transactions = Payments()
            all_transactions.update({
                'key': all_transactions_hash,
                'transaction_ids': ','.join(transaction_ids),
                'account_id': self.account.id
            })
            all_transactions.save()

        else:
            filter_expression, attr_names, attr_values, key_condition_expression = self.get_transaction_where_condition(amounts)

            all_transactions_hash = self.hash('all_finance_transactions', filter_expression, attr_names, attr_values, key_condition_expression, self.account.id)

            all_transactions = Payments().one(key=all_transactions_hash)

            if all_transactions is not None:
                all_finance_transactions = Transaction.all(id=all_transactions.transaction_ids.split(','))

                self.cache['all_finance_transactions'] = all_finance_transactions
                return all_finance_transactions

            self.cache['all_finance_transactions'] = []

            account_ids = [self.account.id]

            if 'other_accounts' in self.payment_config:
                for other_account in self.payment_config['other_accounts']:
                    provider = Provider.one(name=other_account['provider'])
                    account = Account.one(provider_id=provider.id, name=other_account['name'])

                    account_ids.append(account.id)

            transactions = []

            for account_id in account_ids:
                transactions += Transaction.find(
                    {'account_id': account_id},
                    filter_expression=filter_expression,
                    attr_names=attr_names,
                    attr_values=attr_values,
                    orderby='created_at',
                    orderdir='asc',
                    key_condition_expression=key_condition_expression
                )

            transaction_ids = []

            for transaction in transactions:
                if 'monthly_day' in self.payment_config and transaction.date.day != self.payment_config['monthly_day']:
                    continue

                self.cache['all_finance_transactions'].append(transaction)

                transaction_ids.append(transaction.id)

            all_transactions = Payments()
            all_transactions.update({
                'key': all_transactions_hash,
                'transaction_ids': ','.join(transaction_ids),
                'account_id': self.account.id
            })
            all_transactions.save()

        return self.cache['all_finance_transactions']


    @property
    def total_paid(self):
        if 'total_paid' in self.cache:
            return self.cache['total_paid']

        total = 0

        for row in self.all_finance_transactions:
            total += row.money_out

        self.cache['total_paid'] = total

        return total


    @property
    def num_paid(self):
        return len(self.all_finance_transactions)


    @property
    def remaining(self):
        remaining = self.payment_config['amount']

        for transaction in self.all_finance_transactions:
            remaining -= float(transaction.money_out)

        return remaining
