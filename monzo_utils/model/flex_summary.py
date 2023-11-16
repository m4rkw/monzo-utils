import datetime
import math
from monzo_utils.model.payment import Payment

class FlexSummary(Payment):

    def __init__(self, config, status, total, remaining):
        self.config = config
        self.flex_status = status
        self.flex_total = total
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
