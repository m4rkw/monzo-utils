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
import monzo.endpoints.account
import monzo.endpoints.pot
import monzo.endpoints.transaction
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError
from monzo_utils.lib.log import Log
from monzo_utils.lib.config import Config

class MonzoAPI:

    def __init__(self):
        homedir = pwd.getpwuid(os.getuid()).pw_dir
        monzo_dir = f"{homedir}/.monzo"
        self.token_file = f"{monzo_dir}/tokens"

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

 
    def authenticate(self):
        client = Authentication(
            client_id=Config().client_id,
            client_secret=Config().client_secret,
            redirect_url=Config().redirect_url
        )

        if not sys.stdout.isatty():
            if 'email' in Config().keys:
                os.system("echo '%s'| mail -s 'Monzo auth required' '%s'" % (client.authentication_url, Config().email))
            Log().error('Authentication required, unable to sync.')
            sys.exit(1)

        print("\nAuthentication required, check email or visit:\n")
        print(client.authentication_url)

        if os.path.exists(Config().oauth_token_file):
            os.remove(Config().oauth_token_file)

        while not os.path.exists(Config().oauth_token_file):
            time.sleep(1)

        data = json.loads(open(Config().oauth_token_file).read().rstrip())

        os.remove(Config().oauth_token_file)

        try:
            client.authenticate(authorization_token=data['token'], state_token=data['state'])
        except MonzoAuthenticationError:
            Log().error('State code does not match')
            exit(1)
        except MonzoServerError:
            Log().error('Monzo Server Error')
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

        print("\nwaiting for authorisation...")

        while 1:
            time.sleep(1)

            try:
                self.accounts()
                break
            except MonzoPermissionsError:
                pass


    def get_client(self):
        return Authentication(
            client_id=Config().client_id,
            client_secret=Config().client_secret,
            redirect_url=Config().redirect_url,
            access_token=self.access_token,
            access_token_expiry=self.access_token_expiry,
            refresh_token=self.refresh_token
        )


    def account(self, account_id):
        return monzo.endpoints.account.Account.fetch(self.client, account_id=account_id)


    def accounts(self, first=True):
        for i in range(0, 3):
            try:
                accounts = monzo.endpoints.account.Account.fetch(self.client)

                self.update_tokens()

                return accounts

            except MonzoHTTPError:
                if first:
                    if 'NO_AUTH' in os.environ:
                        raise Exception("token expired")

                    self.authenticate()

                    return self.accounts(False)

                Log().error('auth failed')
                sys.exit(1)
            except MonzoAuthenticationError:
                if first:
                    self.authenticate()

                    return self.accounts(False)

                Log().error("auth failed")
                sys.exit(1)
            except MonzoServerError:
                Log().error("server error")

                if i == 2:
                    sys.exit(1)

                time.sleep(5)

            except TimeoutError:
                Log().error("timeout")

                if i == 2:
                    sys.exit(1)

                time.sleep(5)

        raise Exception("failed to retrieve accounts after 3 attempts")


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
                return monzo.endpoints.transaction.Transaction.fetch(self.client, account_id=account_id, expand=['merchant'])
            except Exception as e:
                error = str(e)

                if i != 2:
                    time.sleep(5)

        Log().error("failed to retrieve transactions: %s" % (error))
        sys.exit(1)


    def pots(self, account_id, first=True):
        try:
            pots = monzo.endpoints.pot.Pot.fetch(self.client, account_id=account_id)
        except MonzoHTTPError:
            if first:
                if 'NO_AUTH' in os.environ:
                    raise Exception("token expired")

                self.authenticate()
                self.client = self.get_client()

                return self.pots(account_id, False)

            Log().error("auth failed")
            sys.exit(1)
        except MonzoAuthenticationError:
            if first:
                self.authenticate()
                self.client = self.get_client()

                return self.pots(account_id, False)

            Log().error("auth failed")
            sys.exit(1)
        except TimeoutError:
            Log().error("timeout")
            sys.exit(1)

        return pots


    def withdraw_credit(self, account_id, pot, credit):
        self.load_tokens()

        self.client = self.get_client()

        pot = monzo.endpoints.pot.Pot.fetch_single(self.client, account_id=account_id, pot_id=pot.pot_id)

        dedupe_code = '%s_%s' % (
            pot.pot_id,
            datetime.datetime.now().strftime('%Y%m%d%H')
        )

        amount = round(credit * 100)

        for i in range(0, 3):
            try:
                monzo.endpoints.pot.Pot.withdraw(self.client, pot=pot, account_id=account_id, amount=amount, dedupe_id=dedupe_code)
                return True
            except Exception as e:
                print("failed to withdraw pot money: %s" % (str(e)))

                if i <2:
                    time.sleep(3)

        return False


    def deposit_to_pot(self, account_id, pot, shortfall):
        self.load_tokens()

        self.client = self.get_client()

        pot = monzo.endpoints.pot.Pot.fetch_single(self.client, account_id=account_id, pot_id=pot.pot_id)

        dedupe_code = '%s_%s' % (
            pot.pot_id,
            datetime.datetime.now().strftime('%Y%m%d%H')
        )

        amount = round(shortfall * 100)

        for i in range(0, 3):
            try:
                monzo.endpoints.pot.Pot.deposit(self.client, pot=pot, account_id=account_id, amount=amount, dedupe_id=dedupe_code)
                return True
            except Exception as e:
                print("failed to withdraw pot money: %s" % (str(e)))

                if i <2:
                    time.sleep(3)

        return False
