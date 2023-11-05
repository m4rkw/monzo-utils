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
from monzo.authentication import Authentication
from monzo.endpoints.account import Account
from monzo.endpoints.pot import Pot
from monzo.endpoints.transaction import Transaction
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError
from monzo_db import DB

PROVIDER = 'Monzo'

class Monzo:

    def __init__(self, no_init=False):
        homedir = pwd.getpwuid(os.getuid()).pw_dir
        monzo_dir = f"{homedir}/.monzo"

        if not os.path.exists(monzo_dir):
            os.mkdir(monzo_dir, 0o755)

        self.config_file = f"{monzo_dir}/config.yaml"
        self.token_file = f"{monzo_dir}/tokens"

        if no_init:
            return

        if not os.path.exists(self.config_file):
            sys.stderr.write(f"config file not found: {self.config_file}, run setup first.\n")
            sys.exit(1)

        try:
            self.config = yaml.safe_load(open(self.config_file).read())
        except Exception as e:
            sys.stderr.write(f"could not read config file: {self.config_file}, {str(e)}\n")
            sys.exit(1)

        self.db = DB(self.config['db'])

        self.provider = self.get_provider()

        self.load_tokens()

        self.client = self.get_client()


    def load_tokens(self):
        if os.path.exists(self.token_file):
            data = json.loads(open(self.token_file).read())

            self.access_token = data['access_token']
            self.access_token_expiry = data['expiry']
            self.refresh_token = data['refresh_token']
        else:
            self.authenticate()

 
    def setup(self):
        print("\n========================")
        print("Monzo Utils Setup Wizard")
        print("========================\n")
        print("Requirements:\n")
        print("1) You must have created an OAuth client here: https://developers.monzo.com/apps/new")
        print("   Note: confidentiality must be set to Confidential\n")
        print("2) The MySQL database must be ready (see README.md)\n")
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

        mysql_host = self.prompt_input('MySQL host', '127.0.0.1')
        mysql_port = self.prompt_input('MySQL port', '3306', False, 'int')
        mysql_db = self.prompt_input('MySQL database', 'monzo')
        mysql_user = self.prompt_input('MySQL username', 'monzo')
        mysql_password = self.prompt_input('MySQL password', 'monzo')

        db = {
            'host': mysql_host,
            'port': mysql_port,
            'user': mysql_user,
            'password': mysql_password,
            'database': mysql_db
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

        self.config = {
            'oauth_token_file': token_path,
            'db': db,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_url': redirect_url,
            'email': email
        }

        self.save_config()

        self.__init__()

        self.scan_accounts()

        sys.stdout.write("Performing initial transaction sync ...\n\n")
        sys.stdout.flush()

        self.sync()

        sys.stdout.write("Setup complete!\n\n")


    def save_config(self):
        with open(self.config_file, 'w') as f:
            f.write(yaml.dump(self.config))


    def scan_accounts(self):
        sys.stdout.write("\nFinding accounts...\n\n")

        accounts = Account.fetch(self.client)

        found_accounts = []

        for account in accounts:
            if account.balance is None:
                continue

            if 'accounts' in self.config and account.account_id in self.config['accounts']:
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

            if 'accounts' not in self.config:
                self.config['accounts'] = {}

            self.config['accounts'][account.account_id] = {
                'name': account_name
            }

            if account_type == 'Flex':
                self.config['accounts'][account.account_id]['credit_limit'] = self.prompt_input('credit limit', None, False, 'int')
            else:
                self.config['accounts'][account.account_id]['sortcode'] = self.prompt_input('sort code')
                self.config['accounts'][account.account_id]['account_no'] = self.prompt_input('account no')

            sys.stdout.write("\n")

            self.save_config()


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
        except:
            print("failed")

        try:
            resp = db.query("show tables")
        except Exception as e:
            sys.stderr.write(f"\nFailed to connect to the database: {str(e)}\n\n")
            sys.exit(1)


    def authenticate(self):
        client = Authentication(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            redirect_url=self.config['redirect_url']
        )

        if not sys.stdout.isatty():
            if 'email' in self.config:
                os.system("echo '%s'| mail -s 'Monzo auth required' '%s'" % (client.authentication_url, self.config['email']))
            sys.stderr.write('Authentication required, unable to sync.\n')
            sys.exit(1)

        print("\nAuthentication required, check email or visit:\n")
        print(client.authentication_url)

        if os.path.exists(self.config['oauth_token_file']):
            os.remove(self.config['oauth_token_file'])

        while not os.path.exists(self.config['oauth_token_file']):
            time.sleep(1)

        data = json.loads(open(self.config['oauth_token_file']).read().rstrip())

        os.remove(self.config['oauth_token_file'])

        try:
            client.authenticate(authorization_token=data['token'], state_token=data['state'])
        except MonzoAuthenticationError:
            print('State code does not match')
            exit(1)
        except MonzoServerError:
            print('Monzo Server Error')
            exit(1)

        with open(self.token_file,'w') as f:
            f.write(json.dumps({
                'access_token': client.access_token,
                'expiry': client.access_token_expiry,
                'refresh_token': client.refresh_token
            }))

        self.access_token = client.access_token
        self.access_token_expiry = client.access_token_expiry
        self.refresh_token = client.refresh_token

        self.client = self.get_client()

        print("\n waiting for authorisation...")

        while 1:
            time.sleep(1)

            try:
                self.accounts()
                break
            except MonzoPermissionsError:
                pass


    def get_client(self):
        return Authentication(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            redirect_url=self.config['redirect_url'],
            access_token=self.access_token,
            access_token_expiry=self.access_token_expiry,
            refresh_token=self.refresh_token
        )


    def account(self, account_id):
        return Account.fetch(self.client, account_id=account_id)


    def accounts(self, first=True):
        try:
            accounts = Account.fetch(self.client)
        except MonzoHTTPError:
            if first:
                if 'NO_AUTH' in os.environ:
                    raise Exception("token expired")

                self.authenticate()

                return self.accounts(False)

            print("auth failed")
            sys.exit(1)
        except MonzoAuthenticationError:
            if first:
                self.authenticate()

                return self.accounts(False)

            print("auth failed")
            sys.exit(1)
        except MonzoServerError:
            print("server error")
            sys.exit(1)
        except TimeoutError:
            print("timeout")
            sys.exit(1)

        self.update_tokens()

        return accounts


    def update_tokens(self):
        if self.access_token == self.client.access_token and \
            self.access_token_expiry == self.client.access_token_expiry and \
            self.refresh_token == self.client.refresh_token:
            return

        self.access_token = self.client.access_token
        self.access_token_expiry = self.client.access_token_expiry
        self.refresh_token = self.client.refresh_token

        with open(self.token_file + '.new','w') as f:
            f.write(json.dumps({
                'access_token': self.client.access_token,
                'expiry': self.client.access_token_expiry,
                'refresh_token': self.client.refresh_token
            }))

        os.rename(self.token_file + '.new', self.token_file)


    def transactions(self, account_id):
        error = None

        for i in range(0, 3):
            try:
                transactions = Transaction.fetch(self.client, account_id=account_id, expand=['merchant'])
                return transactions
            except Exception as e:
                error = str(e)

                if i != 2:
                    time.sleep(5)

        print("failed to retrieve transactions: %s" % (error))
        sys.exit(1)


    def pots(self, account_id, first=True):
        try:
            pots = Pot.fetch(self.client, account_id=account_id)
        except MonzoHTTPError:
            if first:
                if 'NO_AUTH' in os.environ:
                    raise Exception("token expired")

                self.authenticate()
                self.client = self.get_client()

                return self.pots(account_id, False)

            print("auth failed")
            sys.exit(1)
        except MonzoAuthenticationError:
            if first:
                self.authenticate()
                self.client = self.get_client()

                return self.pots(account_id, False)

            print("auth failed")
            sys.exit(1)
        except TimeoutError:
            print("timeout")
            sys.exit(1)

        return pots


    def get_or_create_merchant(self, merchant):
        mer = self.db.one("select * from merchant where merchant_id = %s", [merchant['id']])

        if 'metadata' in merchant and 'website' in merchant['metadata']:
            website = merchant['metadata']['website']
        else:
            website = None

        merchant['merchant_id'] = merchant['id']
        merchant.pop('id')
        address = merchant.pop('address')

        if mer:
            mer = self.db.update('merchant', mer['id'], merchant)

            address['merchant_id'] = mer['id']

            addr = self.db.one("select * from merchant_address where merchant_id = %s", [mer['id']])

            if addr:
                self.db.update('merchant_address', addr['id'], address)
            else:
                self.db.create('merchant_address', address)
        else:
            mer = self.db.create('merchant', merchant)

            address['merchant_id'] = mer['id']

            self.db.create('merchant_address', address)

        return mer


    def sanitise(self, string):
        return re.sub('[\s\t]+', ' ', string)


    def add_transaction(self, a, tr, pot_account_ids, pot_id=None):
        if tr.counterparty:
            counterparty = self.get_or_create_counterparty(tr.counterparty)
            counterparty_id = counterparty['id']

            if counterparty['name'] != tr.description:
                description = self.sanitise('%s %s' % (counterparty['name'], tr.description))
            else:
                description = tr.description
        else:
            counterparty_id = None

            description = self.sanitise(tr.description)

        amount = tr.amount

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

        sql = "select * from transaction where account_id = %s and transaction_id = %s and "
        params = [a['id'], tr.transaction_id]

        if pot_id:
            sql += "pot_id = %s"
            params.append(pot_id)
        else:
            sql += "pot_id is null"

        t = self.db.one(sql, params)

        if pot_id is None and tr.metadata and 'pot_account_id' in tr.metadata and tr.metadata['pot_account_id'] not in pot_account_ids:
            pot_account_ids[tr.metadata['pot_account_id']] = tr.metadata['pot_id']

        if tr.merchant:
            merchant = self.get_or_create_merchant(tr.merchant)
        else:
            merchant = None

        obj = {
            'account_id': a['id'],
            'transaction_id': tr.transaction_id,
            'date': tr.created.strftime('%Y-%m-%d'),
            'type': _type,
            'description': description,
            'ref': tr.description,
            'money_in': money_in,
            'money_out': money_out,
            'pending': tr.amount_is_pending,
            'created_at': tr.created,
            'updated_at': tr.updated,
            'currency': tr.currency,
            'local_currency': tr.local_currency,
            'local_amount': tr.local_amount,
            'merchant_id': merchant['id'] if merchant else None,
            'notes': tr.notes,
            'originator': tr.originator,
            'scheme': tr.scheme,
            'settled': tr.settled,
            'declined': 1 if len(tr.decline_reason) >0 else 0,
            'decline_reason': tr.decline_reason,
            'counterparty_id': counterparty_id,
            'pot_id': pot_id
        }

        if t:
            t = self.db.update('transaction', t['id'], obj)

        else:
            t = self.db.create('transaction', obj)

        metadata = {}

        if type(tr.atm_fees_detailed) == dict:
            for key in tr.atm_fees_detailed:
                metadata['atm_fees_detailed_%s' % (key)] = tr.atm_fees_detailed[key]

        if type(tr.categories) == dict:
            for key in tr.categories:
                metadata['categories_%s' % (key)] = tr.categories[key]

        if type(tr.fees) == dict:
            for key in tr.fees:
                metadata['fees_%s' % (key)] = tr.fees[key]

        if type(tr.metadata) == dict:
            for key in tr.metadata:
                metadata['metadata_%s' % (key)] = tr.metadata[key]

        for key in metadata:
            met = self.db.one("select * from transaction_metadata where transaction_id = %s and `key` = %s", [t['id'], key])

            if met:
                self.db.query("update transaction_metadata set `value` = %s where id = %s", [metadata[key], met['id']])
            else:
                self.db.query("insert into transaction_metadata (transaction_id, `key`, `value`) VALUES(%s,%s,%s)", [t['id'], key, metadata[key]])

        for row in self.db.query("select * from transaction_metadata where transaction_id = %s", [t['id']]):
            if row['key'] not in metadata:
                self.db.query("delete from transaction_metadata where id = %s", [row['id']])

        return t


    def get_or_create_counterparty(self, data):
        counterparty = self.db.one("select * from counterparty where user_id = %s", [data['user_id']])

        if counterparty:
            counterparty = self.db.update('counterparty', counterparty['id'], data)
        else:
            counterparty = self.db.create('counterparty', data)

        return counterparty


    def get_provider(self):
        provider = self.db.one("select * from provider where name = %s", [PROVIDER])

        if not provider:
            self.db.query("insert into provider (name) values (%s)", [PROVIDER])
            provider = self.db.one("select * from provider where name = %s", [PROVIDER])

        return provider


    def sync(self):
        a = self.accounts()

        accounts = []

        for acc in a:
            if 'monzoflexbackingloan' in acc.description:
                continue

            a = self.get_or_create_account(acc, self.config['accounts'][acc.account_id])

            try:
                transactions = self.transactions(acc.account_id)
            except MonzoPermissionsError:
                continue
            except MonzoServerError:
                continue

            pots = self.pots(account_id=acc.account_id)

            pot_lookup = {}

            for pot in pots:
                p = self.db.one("select * from pot where account_id = %s and pot_id = %s", [a['id'], pot.pot_id])

                obj = {
                    'account_id': a['id'],
                    'name': pot.name,
                    'balance': pot.balance/100,
                    'pot_id': pot.pot_id,
                    'deleted': pot.deleted
                }

                if not p:
                    p = self.db.create('pot', obj)
                else:
                    p = self.db.update('pot', p['id'], obj)

                pot_lookup[pot.pot_id] = p['id']

            seen = {}

            pot_account_ids = {}

            for tr in transactions:
                t = self.add_transaction(a, tr, pot_account_ids)

                seen[t['id']] = 1

            seen = {}

            for pot_account_id in pot_account_ids:
                transactions = self.transactions(pot_account_id)

                for tr in transactions:
                    t = self.add_transaction(a, tr, pot_account_ids, pot_lookup[pot_account_ids[pot_account_id]])

                    seen[t['id']] = 1

        if 'touch_file' in self.config:
            Path(self.config['touch_file']).touch()


    def get_or_create_account(self, api_account, account_config):
        a = self.db.one("select * from account where account_id = %s", [api_account.account_id])

        account = {
            'provider_id': self.provider['id'],
            'name': account_config['name'],
            'account_id': api_account.account_id
        }

        if 'sortcode' in account_config:
            account['type'] = 'bank'
            account['balance'] = account['available'] = api_account.balance.balance / 100
            account['sortcode'] = account_config['sortcode']
            account['account_no'] = account_config['account_no']
        else:
            account['type'] = 'credit'
            account['balance'] = 0 - (api_account.balance.balance / 100)
            account['available'] = account_config['credit_limit'] - account['balance']

        if not a:
            a = self.db.create('account', account)
        else:
            a = self.db.update('account', a['id'], account)

        return a


    def withdraw_credit(self, account_id, pot, credit):
        if os.path.exists(self.token_file):
            data = json.loads(open(self.token_file).read())

            self.access_token = data['access_token']
            self.access_token_expiry = data['expiry']
            self.refresh_token = data['refresh_token']
        else:
            raise Exception("need to abstract the auth library")

        self.client = self.get_client()

        pot = Pot.fetch_single(self.client, account_id=account_id, pot_id=pot['pot_id'])

        dedupe_code = '%s_%s' % (
            pot.pot_id,
            datetime.datetime.now().strftime('%Y%m%d%H')
        )

        amount = round(credit * 100)

        for i in range(0, 3):
            try:
                Pot.withdraw(self.client, pot=pot, account_id=account_id, amount=amount, dedupe_id=dedupe_code)
                self.sync()
                return True
            except Exception as e:
                print("failed to withdraw pot money: %s" % (str(e)))

                if i <2:
                    time.sleep(3)

        return False


    def deposit_to_pot(self, account_id, pot, shortfall):
        if os.path.exists(self.token_file):
            data = json.loads(open(self.token_file).read())

            self.access_token = data['access_token']
            self.access_token_expiry = data['expiry']
            self.refresh_token = data['refresh_token']
        else:
            raise Exception("need to abstract the auth library")

        self.client = self.get_client()

        pot = Pot.fetch_single(self.client, account_id=account_id, pot_id=pot['pot_id'])

        dedupe_code = '%s_%s' % (
            pot.pot_id,
            datetime.datetime.now().strftime('%Y%m%d%H')
        )

        amount = round(shortfall * 100)

        for i in range(0, 3):
            try:
                Pot.deposit(self.client, pot=pot, account_id=account_id, amount=amount, dedupe_id=dedupe_code)
                self.sync()
                return True
            except Exception as e:
                print("failed to withdraw pot money: %s" % (str(e)))

                if i <2:
                    time.sleep(3)

        return False
