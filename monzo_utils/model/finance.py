from monzo_utils.lib.config import Config
from monzo_utils.model.payment import Payment
from monzo_utils.model.transaction import Transaction

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

        amounts = [int(self.payment_config['amount'] / self.payment_config['months'] * 100) / 100]

        final_payment = round(self.payment_config['amount'] - (amounts[0] * (self.payment_config['months']-1)), 2)

        if final_payment not in amounts:
            amounts.append(final_payment)

        if 'single_payment' in self.payment_config and self.payment_config['single_payment']:
            where, params = self.get_transaction_where_condition(amounts=False)

            self.cache['all_finance_transactions'] = Transaction().find(
                f"select * from transaction where {where} order by created_at asc",
                params
            )
        else:
            where, params = self.get_transaction_where_condition(amounts)

            self.cache['all_finance_transactions'] = Transaction().find(
                f"select * from transaction where {where} order by created_at asc",
                params
            )

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
