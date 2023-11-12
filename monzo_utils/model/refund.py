import datetime
import math
from monzo_utils.model.payment import Payment
from monzo_utils.model.transaction import Transaction

class Refund(Payment):

    transaction_type = 'money_in'
    always_fixed = True

    @property
    def status(self):
        if self.last_payment:
            return 'PAID'

        if self.due_date and self.due_date >= self.next_salary_date:
            return 'SKIPPED'

        if self.payment_config['due_after'] >= self.next_salary_date:
            return 'SKIPPED'

        return 'DUE'
