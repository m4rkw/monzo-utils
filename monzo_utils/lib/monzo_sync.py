#!/usr/bin/env python3

import os
import sys
import time
import json
import yaml
import re
import datetime
import pwd
from pathlib import Path
from monzo_utils.lib.config import Config
from monzo_utils.lib.db import DB
from monzo_utils.lib.log import Log
from monzo_utils.lib.monzo_api import MonzoAPI
from monzo_utils.model.provider import Provider
from monzo_utils.model.account import Account
from monzo_utils.model.merchant import Merchant
from monzo_utils.model.merchant_address import MerchantAddress
from monzo_utils.model.pot import Pot
from monzo_utils.model.transaction import Transaction
from monzo_utils.model.counterparty import Counterparty
from monzo_utils.model.transaction_metadata import TransactionMetadata
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError

PROVIDER = 'Monzo'

class MonzoSync:

    def __init__(self, no_init=False):
        homedir = pwd.getpwuid(os.getuid()).pw_dir
        self.monzo_dir = f"{homedir}/.monzo"

        if not os.path.exists(self.monzo_dir):
            os.mkdir(self.monzo_dir, 0o755)

        self.config_file = f"{self.monzo_dir}/config.yaml"
        self.token_file = f"{self.monzo_dir}/tokens"

        if no_init:
            return

        Config()

        self.api = MonzoAPI()

        self.db = DB()

        self.provider = self.get_provider()


    def setup(self):
        print("\n========================")
        print("Monzo Utils Setup Wizard")
        print("========================\n")
        print("Requirements:\n")
        print("1) You must have created an OAuth client here: https://developers.monzo.com/apps/new")
        print("   Note: confidentiality must be set to Confidential\n")
        print("2) The database (MySQL/MariaDB or SQLite3) must be created and ready (see README.md)\n")
        print("3) The machine we are running on must be reachable on a known port from the internet.")
        print("   The webserver must be configured with the CGI script to capture the oauth tokens.")
        print("   This is only required during setup for the initial oauth authentication flow.")
        print("   Once this is complete and the tokens are stored this can be removed.\n")

        self.prompt_continue()

        if os.path.exists(self.config_file):
            sys.stdout.write(f"\nWARNING! Config file already exists at: {self.config_file}\n\n")
            sys.stdout.write("If we continue this will be erased.\n\n")

            self.prompt_continue()

        sys.stdout.write("\n")

        sys.stdout.write("Which database do you want to use?\n\n")
        sys.stdout.write("1. MySQL/MariaDB (recommended)\n")
        sys.stdout.write("2. SQLite3\n\n")

        while 1:
            db_backend = self.prompt_input('DB choice')

            if db_backend in ['1','2']:
                break

        if db_backend == '1':
            mysql_host = self.prompt_input('MySQL host', '127.0.0.1')
            mysql_port = self.prompt_input('MySQL port', '3306', False, 'int')
            mysql_db = self.prompt_input('MySQL database', 'monzo')
            mysql_user = self.prompt_input('MySQL username', 'monzo')
            mysql_password = self.prompt_input('MySQL password', 'monzo')

            db = {
                'driver': 'mysql',
                'host': mysql_host,
                'port': mysql_port,
                'user': mysql_user,
                'password': mysql_password,
                'database': mysql_db
            }
        else:
            db = {
                'driver': 'sqlite',
                'path': f"{self.monzo_dir}/data.db"
            }

        self.test_db_access(db)

        sys.stdout.write("\n")

        client_id = self.prompt_input('Monzo Client ID')
        client_secret = self.prompt_input('Monzo Client Secret')
        redirect_url = self.prompt_input('Monzo Client redirect URL')

        sys.stdout.write("Enter the path where the CGI script will store the token file:\n")

        token_path = self.prompt_input('Token path', '/var/www/monzo/token')

        sys.stdout.write("\nIf the auth token expires or stops working the sync script can send\n")
        sys.stdout.write("an email to notify you. Enter this email below or leave blank if not required.\n")

        email = self.prompt_input('Email', None, True)

        Config({
            'oauth_token_file': token_path,
            'db': db,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_url': redirect_url,
            'email': email
        })

        Config().save()

        self.__init__()

        self.scan_accounts()

        sys.stdout.write("Performing initial transaction sync ...\n\n")
        sys.stdout.flush()

        self.sync()

        sys.stdout.write("\nSetup complete!\n\n")


    def scan_accounts(self):
        sys.stdout.write("\nFinding accounts...\n\n")

        accounts = self.api.accounts()

        found_accounts = []

        for account in accounts:
            if account.balance is None:
                continue

            if 'accounts' in Config().keys and account.account_id in Config().accounts:
                continue

            if 'Joint account between' in account.description:
                account_type = 'Joint Current Account'
            else:
                account_type = account.account_type()

            print(f"         id: {account.account_id}")
            print(f"    balance: £{account.balance.balance/100:.2f}")
            print(f"description: {account.description}")
            print(f"       type: {account_type}")

            sys.stdout.write("\n")

            resp = self.prompt_continue('Sync this account? [y/N] ', True)

            if resp == 'n':
                continue

            account_name = self.prompt_input('name for this account')

            if 'accounts' not in Config().keys:
                Config().set('accounts', {})

            Config().accounts[account.account_id] = {
                'name': account_name
            }

            if account_type == 'Flex':
                Config().accounts[account.account_id]['credit_limit'] = self.prompt_input('credit limit', None, False, 'int')
            else:
                Config().accounts[account.account_id]['sortcode'] = self.prompt_input('sort code')
                Config().accounts[account.account_id]['account_no'] = self.prompt_input('account no')

            sys.stdout.write("\n")

            Config().save()


    def prompt_continue(self, prompt='Continue? [y/N] ', boolean=False):
        while 1:
            sys.stdout.write(prompt)
            sys.stdout.flush()

            resp = sys.stdin.readline().rstrip().lower()

            if resp == 'n':
                if boolean:
                    return False

                print("\nStopping at user request.\n")
                sys.exit(0)

            if resp == 'y':
                break

        return True

 
    def prompt_input(self, prompt, default=None, none_allowed=False, validation=None):
        while 1:
            if default is None:
                sys.stdout.write(f"Enter {prompt}: ")
            else:
                sys.stdout.write(f"Enter {prompt} [{default}]: ")

            sys.stdout.flush()

            resp = sys.stdin.readline().rstrip()

            if len(resp) == 0:
                if default is None and none_allowed is False:
                    continue

                resp = default

            if validation == 'int' and resp is not None:
                try:
                    resp = int(resp)
                except:
                    sys.stderr.write("\nerror: value must be an integer\n\n")
                    sys.stderr.flush()
                    continue

            return resp


    def test_db_access(self, db_config):
        try:
            db = DB(db_config)
        except Exception as e:
            Log().error(f"failed to initialise the database: {str(e)}")
            sys.exit(1)

        try:
            if db_config['driver'] == 'mysql':
                resp = db.query("show tables")
            else:
                resp = db.query("pragma table_info(`provider`)")

        except Exception as e:
            Log().error(f"Failed to connect to the database: {str(e)}")
            sys.exit(1)


    def get_or_create_merchant(self, mo_merchant):
        if 'metadata' in mo_merchant and 'website' in mo_merchant['metadata']:
            website = mo_merchant['metadata']['website']
        else:
            website = None

        merchant_id = mo_merchant['id']

        mo_merchant['merchant_id'] = mo_merchant['id']
        mo_merchant.pop('id')
        mo_address = mo_merchant.pop('address')

        merchant = Merchant().find_by_merchant_id(merchant_id)

        if not merchant:
            Log().info(f"creating merchant: {mo_merchant['name']} ({mo_merchant['merchant_id']})")
            merchant = Merchant()

        merchant.update(mo_merchant)
        merchant.save()

        mo_address['merchant_id'] = merchant.id

        address = MerchantAddress().find_by_merchant_id(merchant.id)

        if not address:
            address = MerchantAddress()

        address.update(mo_address)
        address.save()

        return merchant


    def sanitise(self, string):
        return re.sub('[\s\t]+', ' ', string)


    def add_transaction(self, account, mo_transaction, pot_account_ids, pot_id=None):
        counterparty = None

        if mo_transaction.counterparty:
            counterparty = self.get_or_create_counterparty(mo_transaction.counterparty)

            if counterparty.name != mo_transaction.description:
                description = self.sanitise('%s %s' % (counterparty.name, mo_transaction.description))
            else:
                description = mo_transaction.description
        else:
            description = self.sanitise(mo_transaction.description)

        amount = mo_transaction.amount

        if amount >0:
            money_in = amount / 100
            money_out = None
            verb = 'from'
            _type = 'credit'
        else:
            money_in = None
            money_out = 0 - (amount / 100)
            verb = 'to'
            _type = 'debit'

        if pot_id:
            where = [{
                'clause': 'pot_id = %s',
                'params': [pot_id]
            }]
        else:
            where = [{
                'clause': 'pot_id is null'
            }]

        transaction = Transaction().find_by_account_id_and_transaction_id(
            account.id,
            mo_transaction.transaction_id,
            where=where
        )

        date = mo_transaction.created.strftime('%Y-%m-%d')

        if not transaction:
            Log().info(f"creating transaction: {account.name} {date} -{money_in} +{money_out} {description}")

            transaction = Transaction()

        if pot_id is None and mo_transaction.metadata and 'pot_account_id' in mo_transaction.metadata and mo_transaction.metadata['pot_account_id'] not in pot_account_ids:
            pot_account_ids[mo_transaction.metadata['pot_account_id']] = mo_transaction.metadata['pot_id']

        if mo_transaction.merchant:
            merchant = self.get_or_create_merchant(mo_transaction.merchant)
        else:
            merchant = None

        transaction.update({
            'account_id': account.id,
            'transaction_id': mo_transaction.transaction_id,
            'date': date,
            'type': _type,
            'description': description,
            'ref': mo_transaction.description,
            'money_in': money_in,
            'money_out': money_out,
            'pending': mo_transaction.amount_is_pending,
            'created_at': mo_transaction.created,
            'updated_at': mo_transaction.updated,
            'currency': mo_transaction.currency,
            'local_currency': mo_transaction.local_currency,
            'local_amount': mo_transaction.local_amount,
            'merchant_id': merchant.id if merchant else None,
            'notes': mo_transaction.notes,
            'originator': mo_transaction.originator,
            'scheme': mo_transaction.scheme,
            'settled': mo_transaction.settled,
            'declined': 1 if len(mo_transaction.decline_reason) >0 else 0,
            'decline_reason': mo_transaction.decline_reason,
            'counterparty_id': counterparty.id if counterparty else None,
            'pot_id': pot_id
        })

        transaction.save()

        metadata = {}

        if type(mo_transaction.atm_fees_detailed) == dict:
            for key in mo_transaction.atm_fees_detailed:
                metadata['atm_fees_detailed_%s' % (key)] = mo_transaction.atm_fees_detailed[key]

        if type(mo_transaction.categories) == dict:
            for key in mo_transaction.categories:
                metadata['categories_%s' % (key)] = mo_transaction.categories[key]

        if type(mo_transaction.fees) == dict:
            for key in mo_transaction.fees:
                metadata['fees_%s' % (key)] = mo_transaction.fees[key]

        if type(mo_transaction.metadata) == dict:
            for key in mo_transaction.metadata:
                metadata['metadata_%s' % (key)] = mo_transaction.metadata[key]

        for key in metadata:
            transaction_metadata = TransactionMetadata().find_by_transaction_id_and_key(transaction.id, key)

            if not transaction_metadata:
                transaction_metadata = TransactionMetadata()
                transaction_metadata.transaction_id = transaction.id
                transaction_metadata.key = key

            transaction_metadata.value = metadata[key]

            transaction_metadata.save()

        for transaction_metadata in TransactionMetadata().find_all_by_transaction_id(transaction.id):
            if transaction_metadata.key not in metadata:
                transaction_metadata.delete()

        return transaction


    def get_or_create_counterparty(self, mo_counterparty):
        counterparty = Counterparty().find_by_user_id(mo_counterparty['user_id'])

        if not counterparty:
            Log().info(f"creating counterparty: {mo_counterparty['name']} ({mo_counterparty['user_id']})")
            counterparty = Counterparty()

        counterparty.update(mo_counterparty)

        counterparty.save()

        return counterparty


    def get_provider(self):
        provider = Provider().find_by_name(PROVIDER)

        if not provider:
            Log().info(f"creating provider: {PROVIDER}")

            provider = Provider()
            provider.name = PROVIDER
            provider.save()

        return provider


    def sync(self):
        mo_accounts = self.api.accounts()

        accounts = []

        for mo_account in mo_accounts:
            if 'monzoflexbackingloan' in mo_account.description:
                continue

            account = self.get_or_create_account(mo_account, Config().accounts[mo_account.account_id])

            Log().info(f"syncing account: {account.name}")

            Log().info(f"getting pots for account: {account.name}")

            mo_pots = self.api.pots(account_id=account.account_id)

            pot_lookup = {}

            for mo_pot in mo_pots:
                pot = Pot().find_by_account_id_and_pot_id(account.id, mo_pot.pot_id)

                if not pot:
                    Log().info(f"creating pot: {mo_pot.name}")
                    pot = Pot()

                pot.account_id = account.id
                pot.pot_id = mo_pot.pot_id
                pot.name = mo_pot.name
                pot.balance = mo_pot.balance / 100
                pot.deleted = mo_pot.deleted

                pot.save()

                pot_lookup[pot.pot_id] = pot
 
            try:
                Log().info(f'syncing transactions for account: {account.name}')

                mo_transactions = self.api.transactions(account.account_id)
            except MonzoPermissionsError as e:
                Log().error(f"permissions error: {str(e)}")
                continue
            except MonzoServerError as e:
                Log().error(f"server error: {str(e)}")
                continue

            seen = {}
            total = 0

            pot_account_ids = {}

            for mo_transaction in mo_transactions:
                transaction = self.add_transaction(account, mo_transaction, pot_account_ids)

                seen[transaction.id] = 1
                total += 1

            seen = {}

            for pot_account_id in pot_account_ids:
                if pot_lookup[pot_account_ids[pot_account_id]].deleted:
                    continue

                Log().info(f"syncing transactions for pot: {pot_lookup[pot_account_ids[pot_account_id]].name}")

                mo_pot_transactions = self.api.transactions(pot_account_id)

                for mo_pot_transaction in mo_pot_transactions:
                    transaction = self.add_transaction(account, mo_pot_transaction, pot_account_ids, pot_lookup[pot_account_ids[pot_account_id]].id)

                    seen[transaction.id] = 1
                    total += 1

            Log().info(f"account {account.name} synced {total} transactions")

        if 'touch_file' in Config().keys:
            Path(Config().touch_file).touch()


    def get_or_create_account(self, mo_account, account_config):
        account = Account().find_by_provider_id_and_account_id(self.provider.id, mo_account.account_id)

        if not account:
            account = Account()

        account.provider_id = self.provider.id
        account.name = account_config['name']
        account.account_id = mo_account.account_id

        if 'sortcode' in account_config:
            account.type = 'bank'
            account.balance = account.available = mo_account.balance.balance / 100
            account.sortcode = account_config['sortcode']
            account.account_no = account_config['account_no']
        else:
            account.type = 'credit'
            account.balance = 0 - (mo_account.balance.balance / 100)
            account.available = account_config['credit_limit'] - account.balance
            account.credit_limit = account_config['credit_limit']

        account.save()

        return account
