import datetime
from monzo_utils.model.finance import Finance

class AmazonPayments(Finance):

    @property
    def due_date(self):
        if len(self.all_finance_transactions) == self.payment_config['months']:
            return None

        day = self.today + datetime.timedelta(days=1)

        while day.day != self.payment_list_config['payment_day']:
            day += datetime.timedelta(days=1)

        return datetime.date(day.year, day.month, day.day)
