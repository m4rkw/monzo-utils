#!/usr/bin/env python3

import os
import sys
import datetime
import yaml
import calendar
import json
import time
import requests
import math
import pwd
import importlib
import decimal
from pushover import Client
from monzo_utils.lib.monzo_api import MonzoAPI
from monzo_utils.lib.config import Config
from monzo_utils.lib.db import DB
from monzo_utils.lib.monzo_sync import MonzoSync
from monzo_utils.model.provider import Provider
from monzo_utils.model.account import Account
from monzo_utils.model.pot import Pot
from monzo_utils.model.transaction import Transaction
from monzo_utils.model.flex_summary import FlexSummary
from govuk_bank_holidays.bank_holidays import BankHolidays
from calendar import monthrange

PROVIDER = 'Monzo'

class MonzoPayments:

    def __init__(self, account_name, output_json=False, abbreviate=False):
        self.account_name = account_name
        self.json = output_json
        self.abbreviate = abbreviate
        self.output = []
        self.due = 0
        self.total_this_month = 0
        self.next_month = 0
        self.next_month_bills_pot = 0

        self.config = self.load_config()
        self.validate_config()

        self.db = self.get_db()

        self.seen = []
        self.exchange_rates = {}

        self.provider = Provider("select * from provider where name = %s", [PROVIDER])
        self.account = Account("select * from account where provider_id = %s and name = %s", [self.provider.id, self.account_name])

        if not self.account:
            sys.stderr.write(f"account {self.account_name} not found in the database\n")
            sys.exit(1)

        homedir = pwd.getpwuid(os.getuid()).pw_dir
        self.credit_tracker = f"{homedir}/.monzo/{self.config['account']}.credit"
        self.shortfall_tracker = f"{homedir}/.monzo/{self.config['account']}.shortfall"


    def get_db(self):
        try:
            db = DB(None, self.config_path)
        except Exception as e:
            print(f"failed to connect to the database: {str(e)}")
            sys.exit(1)

        return db


    def load_config(self):
        if os.path.exists(self.account_name):
            account_config_file = self.account_name
            self.config_path = os.path.dirname(account_config_file)
        else:
            homedir = pwd.getpwuid(os.getuid()).pw_dir

            self.config_path = f"{homedir}/.monzo"

            if not os.path.exists(self.config_path):
                if not os.path.exists(self.config_path):
                    os.mkdir(self.config_path, 0o755)

            account_config_file = f"{self.config_path}/{self.account_name}.yaml"

        if not os.path.exists(account_config_file):
            sys.stderr.write(f"Cannot find account config file: {account_config_file}\n")
            sys.exit(1)

        try:
            config = yaml.safe_load(open(account_config_file).read())
        except Exception as e:
            sys.stderr.write(f"Cannot read or parse account config file {account_config_file}: {str(e)}\n")
            sys.exit(1)

        self.account_name = config['account']

        return config


    def validate_config(self):
        for required in ['payments','salary_description','salary_payment_day']:
            if required not in self.config or not self.config[required]:
                sys.stderr.write(f"Missing config key: {required}\n")
                sys.exit(1)

        if ('notify_shortfall' in self.config and self.config['notify_shortfall']) or ('notify_credit' in self.config and self.config['notify_credit']):
            for required in ['pushover_key','pushover_app']:
                if required not in self.config or not self.config[required]:
                    sys.stderr.write(f"Push is enabled but push config key is missing: {required}\n")
                    sys.exit(1)


    def main(self):
        self.last_salary_date = self.get_last_salary_date()
        self.next_salary_date = self.get_next_salary_date(self.last_salary_date)
        self.following_salary_date = self.get_next_salary_date(self.next_salary_date)

        if self.json is False:
            self.display_columns('yearly')

        if 'payments' in self.config:
            for payment_list in self.config['payments']:
                if not payment_list['payments']:
                    continue

                due, total_due_this_month, total_due_next_month = self.display_payment_list(payment_list, True)

                self.due += due
                self.total_this_month += total_due_this_month
                self.next_month += total_due_next_month

            self.display_spacer('monthly')

            for payment_list in self.config['payments']:
                if not payment_list['payments']:
                    continue

                due, total_due_this_month, total_due_next_month = self.display_payment_list(payment_list, False)

                self.due += due
                self.total_this_month += total_due_this_month
                self.next_month += total_due_next_month

        if 'refunds_due' in self.config and self.config['refunds_due']:
            self.display_payment_list({
                'type': 'Refund',
                'payments': self.config['refunds_due']
            }, False)

        if 'pot' in self.config:
            pot = self.account.get_pot(self.config['pot'])
        else:
            pot = self.account

        shortfall = (self.due - (round(pot.balance * 100))) / 100

        if self.json:
            data = {
                'balance': float(pot.balance),
                'due': float(self.due) / 100,
                'total_this_month': self.total_this_month / 100,
                'total_next_month': self.next_month / 100,
                'payments': self.sanitise(self.output)
            }

            if shortfall * 100 <0:
                data['credit'] = (round(pot.balance * 100) - self.due) / 100
                data['shortfall'] = 0
            else:
                data['shortfall'] = shortfall
                data['credit'] = 0

            print(json.dumps(data,indent=4))
            return

        sys.stdout.write("\n")

        sys.stdout.write(" " * 25)
        sys.stdout.write("TOTAL THIS MONTH:".ljust(32))
        print("£%.2f" % (self.total_this_month / 100))

        if 'exclude_yearly_from_bills' in self.config and self.config['exclude_yearly_from_bills']:
            sys.stdout.write("\n")

        sys.stdout.write(" " * 25)
        sys.stdout.write("TOTAL NEXT MONTH:".ljust(32))
        print("£%.2f" % (self.next_month / 100))

        credit = (round(pot.balance * 100) - self.due) / 100

        if round(shortfall * 100) <0:
            sys.stdout.write(" " * 25)
            sys.stdout.write("LESS CREDIT BALANCE:".ljust(32))
            print("£%.2f" % ((self.next_month / 100) - credit))

        if 'exclude_yearly_from_bills' in self.config and self.config['exclude_yearly_from_bills']:
            sys.stdout.write(" " * 25)
            sys.stdout.write("Bills pot payment:".ljust(31))
            print("£%.2f" % (self.next_month_bills_pot / 100))

        sync_required = False

        if round(shortfall * 100) >0:
            print("      due: £%.2f" % (self.due / 100))
            print("  balance: £%.2f" % (pot.balance))
            print("shortfall: £%.2f" % (shortfall))

            sync_required = self.handle_shortfall(pot, shortfall)

        else:

            if os.path.exists(self.shortfall_tracker):
                os.remove(self.shortfall_tracker)

            print("    due: £%.2f" % (self.due / 100))
            print("balance: £%.2f" % (pot.balance))

            if round(credit * 100) == 0:
                credit = 0

                if os.path.exists(self.credit_tracker):
                    os.remove(self.credit_tracker)

            else:
                print(" credit: £%.2f" % (credit))

                sync_required = self.handle_credit(pot, credit)

        today = datetime.datetime.now()

        if today.strftime('%Y%m%d') == self.last_salary_date.strftime('%Y%m%d'):
            if self.check_pot_payments():
                sync_required = True

        if sync_required:
            ms = MonzoSync()
            ms.sync()


    def display_columns(self, title):
        print("%s %s %s %s %s %s %s %s" % (
            'Status'.rjust(8),
            'Type'.ljust(15),
            'Name'.ljust(25),
            ''.ljust(5),
            'Amount'.ljust(19),
            'Left'.ljust(8),
            'Last date'.ljust(12),
            'Due date'.ljust(10)
        ))

        self.display_spacer(title)


    def display_spacer(self, title):
        sys.stdout.write("-" * 9)
        sys.stdout.write(title.ljust(15,'-'))
        sys.stdout.write(("-" * 85) + "\n")


    def prompt_action(self, prompt):
        while 1:
            sys.stdout.write(prompt)
            sys.stdout.flush()

            i = sys.stdin.readline().rstrip().lower()

            if i in ['y','n']:
                break

        return i == 'y'

 
    def display_payment_list(self, payment_list, annual):
        payments = self.get_payments(payment_list, annual)

        summary = None
        due = 0
        total_due_this_month = 0
        total_due_next_month = 0

        if payment_list['type'] == 'Flex':
            total_this_month = 0
            total_next_month = 0
            today = datetime.datetime.now()
            today = datetime.date(today.year, today.month, today.day)

            for payment in payments:
                total_this_month += payment.amount_for_period(self.last_salary_date, self.next_salary_date)
                total_next_month += payment.amount_for_period(self.next_salary_date, self.following_salary_date)

            flex_remaining = 0

            for payment in payments:
                flex_remaining += payment.remaining

            summary = FlexSummary(self.config, total_this_month, total_next_month, flex_remaining, self.last_salary_date, self.next_salary_date, self.following_salary_date)

            if self.json:
                self.output.append(summary.data(self.abbreviate))
            else:
                summary.display()

        for payment in payments:
            if summary:
                payment.last_flex_payment = summary.last_payment

            if payment.status in ['DUE','PAID']:
                total_due_this_month += payment.display_amount * 100

            if payment.status == 'DUE':
                due += payment.display_amount * 100

            if payment.due_next_month:
                if payment.status == 'SKIPPED' or payment_list['type'] != 'Refund':
                    total_due_next_month += payment.next_month_amount * 100

                    if 'exclude_yearly_from_bills' not in self.config or self.config['exclude_yearly_from_bills'] is False or 'yearly_month' not in payment_config:
                        self.next_month_bills_pot += payment.next_month_amount * 100

            if self.json:
                self.output.append(payment.data(self.abbreviate))
            else:
                payment.display()

        return due, total_due_this_month, total_due_next_month


    def get_payments(self, payment_list, annual):
        payments = {}

        for payment_config in payment_list['payments']:
            payment_list_type_library = payment_list['type'].lower().replace(' ','_')
            payment_list_type = payment_list['type'].title().replace(' ','')

            if annual and ('is_yearly' not in payment_config or payment_config['is_yearly'] is False) and ('yearly_month' not in payment_config or 'yearly_day' not in payment_config):
                continue

            if not annual and (('yearly_month' in payment_config and 'yearly_day' in payment_config) or ('is_yearly' in payment_config and payment_config['is_yearly'])):
                continue

            payment = getattr(importlib.import_module(f"monzo_utils.model.{payment_list_type_library}"), payment_list_type)(
                self.config,
                payment_list,
                payment_config,
                self.last_salary_date,
                self.next_salary_date,
                self.following_salary_date
            )

            if payment.due_date not in payments:
                payments[payment.due_date] = []

            payments[payment.due_date].append(payment)

        sorted_payments = []

        for due_date in sorted(payments):
            for payment in payments[due_date]:
                sorted_payments.append(payment)

        return sorted_payments


    def notify(self, event, message):
        pushover = Client(self.config['pushover_key'], api_token=self.config['pushover_app'])
        pushover.send_message(message, title=event)


    def abbreviate_string(self, string):
        abbreviated = ''
        
        for i in range(0, len(string)):
            if string[i].isupper():
                abbreviated += string[i]

        return abbreviated


    def get_last_salary_date(self):
        if 'salary_account' in self.config and self.config['salary_account'] != self.account_name:
            account = Account("select * from account where provider_id = %s and name = %s", [self.provider.id, self.config['salary_account']])
        else:
            account = self.account

        last_salary_transaction = account.last_salary_transaction(
            description=self.config['salary_description'],
            salary_minimum=self.config['salary_minimum'] if 'salary_minimum' in self.config else 1000,
            salary_payment_day=self.config['salary_payment_day']
        )

        if not last_salary_transaction:
            sys.stderr.write("failed to find last salary transaction.\n")
            sys.exit(1)

        last_salary_date = last_salary_transaction['date']

        return last_salary_date


    def get_next_salary_date(self, last_salary_date):
        while last_salary_date.day != self.config['salary_payment_day']:
            try:
                last_salary_date = datetime.date(last_salary_date.year, last_salary_date.month, last_salary_date.day+1)
            except:
                last_salary_date = datetime.date(last_salary_date.year, last_salary_date.month+1, 1)

        next_salary_date = datetime.date(last_salary_date.year, last_salary_date.month, last_salary_date.day+1)

        while next_salary_date.day != self.config['salary_payment_day']:
            try:
                next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month, next_salary_date.day+1)
            except:
                if next_salary_date.month == 12:
                    next_salary_date = datetime.date(next_salary_date.year+1, 1, 1)
                else:
                    next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month+1, 1)

        while next_salary_date.weekday() in [5,6]:
            if next_salary_date.day == 1:
                if next_salary_date.month == 1:
                    next_salary_date = datetime.date(next_salary_date.year-1, 12, 31)
                else:
                    next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month-1, monthrange(next_salary_date.year, next_salary_date.month-1)[1])
            else:
                next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month, next_salary_date.day-1)

        if 'uk_bank_holidays' in self.config and self.config['uk_bank_holidays']:
            bank_holidays = BankHolidays()

            while bank_holidays.is_holiday(next_salary_date) or next_salary_date == datetime.date(2024,4,1) or next_salary_date.weekday() in [5,6]:
                if next_salary_date.day == 1:
                    if next_salary_date.month == 1:
                        next_salary_date = datetime.date(next_salary_date.year-1, 12, 31)
                    else:
                        next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month-1, monthrange(next_salary_date.year, next_salary_date.month-1)[1])
                else:
                    next_salary_date = datetime.date(next_salary_date.year, next_salary_date.month, next_salary_date.day-1)

        return next_salary_date


    def handle_shortfall(self, pot, shortfall):
        deposit = False
        notify = False

        if 'pot' in self.config and 'auto_deposit' in self.config and self.config['auto_deposit'] and not sys.stdout.isatty() and not self.abbreviate:
            if 'auto_deposit_delay_mins' in self.config:
                deposit = self.handle_deposit_delay(shortfall)
            else:
                deposit = True

        elif not sys.stdout.isatty():
            if 'notify_shortfall' in self.config and self.config['notify_shortfall'] and not self.abbreviate:
                notify = True
        else:
            if 'pot' in self.config and 'prompt_deposit' in self.config and self.config['prompt_deposit']:
                deposit = self.prompt_action("\ndeposit shortfall? [y/N] ")

            elif 'notify_shortfall' in self.config and self.config['notify_shortfall']:
                notify = True

        if deposit:
            m = MonzoAPI()

            if not m.deposit_to_pot(self.account.account_id, pot, shortfall):
                sys.stderr.write("ERROR: failed to deposit funds\n")

                if 'notify_deposit' in self.config and self.config['notify_deposit']:
                    self.notify(
                        '%s - pot deposit failed' % (self.account.name),
                        "£%.2f\n£%.2f due, £%.2f available" % (
                            credit,
                            self.due / 100,
                            pot.balance
                        )
                    )
            else:
                if os.path.exists(self.shortfall_tracker):
                    os.remove(shortfall_tracker)

                if 'notify_deposit' in self.config and self.config['notify_deposit']:
                    self.notify(
                        '%s - pot topped up' % (self.account.name),
                        "£%.2f\n£%.2f due, £%.2f available" % (
                            shortfall,
                            self.due / 100,
                            pot.balance
                        )
                    )

                return True

        elif notify:
            self.notify(
                '%s - shortfall' % (self.account.name),
                "£%.2f\n£%.2f due, £%.2f available" % (
                    shortfall,
                    self.due / 100,
                    pot.balance
                )
            )

        return False


    def handle_credit(self, pot, credit):
        withdraw = False
        notify = False

        if 'pot' in self.config and 'auto_withdraw' in self.config and self.config['auto_withdraw'] and not sys.stdout.isatty() and not self.abbreviate:
            if 'auto_withdraw_delay_mins' in self.config:
                withdraw = self.handle_withdrawal_delay(credit)
            else:
                withdraw = True
        elif not sys.stdout.isatty():
            if 'notify_credit' in self.config and self.config['notify_credit'] and not self.abbreviate:
                notify = True
        else:
            if 'pot' in self.config and 'prompt_withdraw' in self.config and self.config['prompt_withdraw']:
                withdraw = self.prompt_action("\nwithdraw credit? [y/N] ")

            elif 'notify_credit' in self.config and self.config['notify_credit']:
                notify = True

        if withdraw:
            m = MonzoAPI()

            if not m.withdraw_from_pot(self.account.account_id, pot, credit):
                sys.stderr.write("ERROR: failed to withdraw credit\n")

                if 'notify_withdraw' in self.config and self.config['notify_withdraw']:
                    self.notify(
                        '%s - pot credit withdraw failed' % (self.account.name),
                        "£%.2f\n£%.2f due, £%.2f available" % (
                            credit,
                            self.due / 100,
                            pot.balance
                        )
                    )
            else:
                if os.path.exists(self.credit_tracker):
                    os.remove(credit_tracker)

                if 'notify_withdraw' in self.config and self.config['notify_withdraw']:
                    self.notify(
                        '%s - pot credit withdrawn' % (self.account.name),
                        "£%.2f\n£%.2f due, £%.2f available" % (
                            credit,
                            self.due / 100,
                            pot.balance
                        )
                    )

                return True

        elif notify:
            self.notify(
                '%s - credit' % (self.account.name),
                "£%.2f\n£%.2f due, £%.2f available" % (
                    credit,
                    self.due / 100,
                    pot.balance
                )
            )

        return False


    def handle_withdrawal_delay(self, credit):
        credit_s = str(int(credit * 100))

        if not os.path.exists(self.credit_tracker) or self.get_file_contents(self.credit_tracker).rstrip() != credit_s:
            with open(self.credit_tracker,'w') as f:
                f.write(credit_s)

            return False

        elapsed = time.time() - os.stat(self.credit_tracker).st_mtime

        return elapsed >= self.config['auto_withdraw_delay_mins'] * 60


    def get_file_contents(self, path):
        return open(path).read()


    def handle_deposit_delay(self, shortfall):
        homedir = pwd.getpwuid(os.getuid()).pw_dir

        shortfall_s = str(int(shortfall * 100))

        if not os.path.exists(self.shortfall_tracker) or self.get_file_contents(self.shortfall_tracker).rstrip() != shortfall_s:
            with open(self.shortfall_tracker,'w') as f:
                f.write(shortfall_s)

            return False

        elapsed = time.time() - os.stat(self.shortfall_tracker).st_mtime

        return elapsed >= self.config['auto_deposit_delay_mins'] * 60


    def sanitise(self, output):
        new_output = []

        for item in output:
            obj = {}
            
            for key in item:
                if type(item[key]) == datetime.date:
                    obj[key] = item[key].strftime('%Y-%m-%d')
                elif type(item[key]) == datetime.datetime:
                    obj[key] = item[key].strftime('%Y-%m-%d %H:%M:%S')
                elif type(item[key]) == decimal.Decimal:
                    obj[key] = float(item[key])
                else:
                    obj[key] = item[key]

            new_output.append(obj)

        return new_output


    def check_pot_payments(self):
        m = None
        sync_required = False

        if 'payments_to_pots' not in self.config or type(self.config['payments_to_pots']) != list:
            return sync_required

        for payment in self.config['payments_to_pots']:
            pot = Pot("select * from pot where name = %s and deleted = %s", [payment['name'], 0])

            if pot.last_monthly_transfer_date != self.last_salary_date:
                amount_to_transfer = self.get_transfer_amount(pot, payment)

                if amount_to_transfer == 0:
                    continue

                if not m:
                    m = MonzoAPI()
                    sys.stdout.write("\n")

                sys.stdout.write("Transferring £%.2f to pot: %s ... " % (amount_to_transfer / 100, pot.name))
                sys.stdout.flush()

                if m.deposit_to_pot(self.account.account_id, pot, amount_to_transfer / 100):
                    sys.stdout.write("OK\n")

                    pot.last_monthly_transfer_date = self.last_salary_date
                    pot.save()

                    sync_required = True
                else:
                    sys.stdout.write("FAILED\n\n")

                    sys.stderr.write("ERROR: failed to transfer £%.2f to pot: %s\n" % (amount_to_transfer / 100, pot.name))

        return sync_required


    def get_transfer_amount(self, pot, payment):
        amount = round(payment['amount'] * 100)

        if 'topup' in payment and payment['topup']:
            pot_balance = round(pot.balance * 100)
            to_transfer = max([0, amount - pot_balance])
        else:
            to_transfer = amount

        return to_transfer


if __name__ == '__main__':
    if len(sys.argv) <2:
        print("usage: %s [-o json] <account_name>" % (sys.argv[0].split('/')[-1]))
        sys.exit(1)

    output_json = False
    account = None
    abbreviate = False

    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-o' and i+1 < len(sys.argv) and sys.argv[i+1] == 'json':
            output_json = True
            continue
        else:
            if sys.argv[i] == '-a':
                abbreviate = True
                continue

            if sys.argv[i-1] == '-o':
                continue

            account = sys.argv[i]

    if account is None:
        print("usage: %s [-o json] [-a] <account_name>" % (sys.argv[0].split('/')[-1]))
        sys.exit(1)

    p = MonzoPayments(account, output_json, abbreviate)
    p.main()
