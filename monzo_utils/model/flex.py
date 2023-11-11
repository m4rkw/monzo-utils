import datetime
import math
from monzo_utils.model.payment import Payment

class Flex(Payment):

    @property
    def name(self):
        return '- ' + self.payment_config['name']


    @property
    def last_date(self):
        return None


    @property
    def due_date(self):
        date_due = self.today + datetime.timedelta(days=1)

        if 'start_date' in self.payment_config:
            date_due = self.payment_config['start_date']

        for i in range(0, self.payment_config['months']):
            while date_due.day != self.config['flex_payment_date']:
                date_due += datetime.timedelta(days=1)

            if date_due > datetime.date(self.today.year, self.today.month, self.today.day):
                return datetime.date(date_due.year, date_due.month, date_due.day)

            date_due += datetime.timedelta(days=1)

        return None


    @property
    def status(self):
        if self.due_date:
            if self.due_date < self.next_salary_date:
                return 'DUE'
            else:
                return 'SKIPPED'
        else:
            return 'DONE'


    @property
    def num_paid(self):
        date = self.payment_config['start_date']
        num_paid = 0

        for i in range(0, self.payment_config['months']):
            while date.day != self.config['flex_payment_date']:
                date += datetime.timedelta(days=1)

            if date <= datetime.date(self.today.year, self.today.month, self.today.day):
                num_paid + 1

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
                num_paid + 1
                total_paid += amount
            else:
                break

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
                num_paid + 1
                total_paid += amount
            else:
                break

        return self.payment_config['amount'] - total_paid
