import datetime
import math
from monzo_utils.model.payment import Payment

class FlexSummary(Payment):

    def __init__(self, config, status, total, total_next_month, remaining):
        self.config = config
        self.flex_status = status
        self.flex_total = total
        self.flex_total_next_month = total_next_month
        self.flex_remaining = remaining


    @property
    def status(self):
        return self.flex_status


    @property
    def name(self):
        return 'Flex Payment'


    @property
    def display_amount(self):
        return self.flex_total


    @property
    def last_date(self):
        last_date = datetime.datetime.now()

        while last_date.day != self.config['flex_payment_date']:
            last_date -= datetime.timedelta(days=1)

        return last_date


    @property
    def due_date(self):
        date = datetime.datetime.now() + datetime.timedelta(days=1)

        while date.day != self.config['flex_payment_date']:
            date += datetime.timedelta(days=1)

        return datetime.date(date.year, date.month, date.day)


    @property
    def remaining(self):
        return self.flex_remaining


    def display(self):
        super().display()

        data = self.data()

        print("%s: %s %s %s %s %s %s %s" % (
            'SKIPPED'.rjust(7),
            data['payment_type'].ljust(15),
            'Flex Payment next month'.ljust(25),
            data['suffix'].ljust(4),
            ('£%.2f' % (self.flex_total_next_month)).ljust(8),
            ('£%.2f' % (data['remaining'] - self.flex_total_next_month)).ljust(8) if data['remaining'] else ''.ljust(8),
            data['last_date'].strftime('%Y-%m-%d').ljust(12) if data['last_date'] else ''.ljust(12),
            data['due_date'].strftime('%Y-%m-%d').ljust(10) if data['due_date'] else ''
        ))
