from base_test import BaseTest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from monzo_utils.lib.db import DB
from monzo_utils.lib.config import Config
from monzo_utils.lib.monzo_api import MonzoAPI
from monzo_utils.model.pot import Pot
from monzo.exceptions import MonzoAuthenticationError, MonzoServerError, MonzoHTTPError, MonzoPermissionsError
import pytest
import os
import pwd
import datetime
from freezegun import freeze_time

class TestMonzoAPI(BaseTest):

    def setUp(self):
        Config._instances = {}
        DB._instances = {}

        if 'NO_AUTH' in os.environ:
            os.environ.pop('NO_AUTH')


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.load_tokens')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    def test_constructor(self, mock_get_client, mock_load_tokens):
        mock_get_client.return_value = 'client'

        api = MonzoAPI()

        homedir = pwd.getpwuid(os.getuid()).pw_dir

        self.assertEqual(api.token_file, f"{homedir}/.monzo/tokens")
        self.assertEqual(api.client, 'client')

        mock_load_tokens.assert_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('os.path.exists')
    def test_load_tokens_no_file(self, mock_exists, mock_authenticate, mock_init):
        mock_init.return_value = None
        mock_exists.return_value = False

        api = MonzoAPI()
        api.token_file = '/tmp/blah'
        api.load_tokens()

        mock_authenticate.assert_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.loads')
    def test_load_tokens_from_file(self, mock_json_load, mock_open, mock_exists, mock_authenticate, mock_init):
        mock_init.return_value = None
        mock_exists.return_value = True
        mock_json_load.return_value = {
            'access_token': 'access token',
            'expiry': 'expiry',
            'refresh_token': 'refresh_token'
        }

        api = MonzoAPI()
        api.token_file = '/tmp/blah'
        api.load_tokens()

        self.assertEqual(api.access_token, 'access token')
        self.assertEqual(api.access_token_expiry, 'expiry')
        self.assertEqual(api.refresh_token, 'refresh_token')


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo.authentication.Authentication.__init__')
    @patch('monzo.authentication.Authentication.authentication_url', new_callable=PropertyMock)
    @patch('os.system')
    def test_authenticate_notify_auth_required_no_email(self, mock_system, mock_auth_url, mock_auth, mock_isatty, mock_init):
        mock_init.return_value = None
        mock_auth.return_value = None
        mock_isatty.return_value = False

        config = Config({
            'client_id': 'test',
            'client_secret': 'test',
            'redirect_url': 'test'
        })

        Config._instances[Config] = config

        api = MonzoAPI()

        with pytest.raises(SystemExit) as e:
            api.authenticate()

        mock_system.assert_not_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('sys.stdout.isatty')
    @patch('monzo.authentication.Authentication.__init__')
    @patch('monzo.authentication.Authentication.authentication_url', new_callable=PropertyMock)
    @patch('os.system')
    def test_authenticate_notify_auth_required_with_email(self, mock_system, mock_auth_url, mock_auth, mock_isatty, mock_init):
        mock_init.return_value = None
        mock_auth.return_value = None
        mock_isatty.return_value = False
        mock_auth_url.return_value = 'https://auth'

        config = Config({
            'client_id': 'test',
            'client_secret': 'test',
            'redirect_url': 'test',
            'email': 'test@test.blah'
        })

        Config._instances[Config] = config

        api = MonzoAPI()

        with pytest.raises(SystemExit) as e:
            api.authenticate()

        mock_system.assert_called_with("echo 'https://auth'| mail -s 'Monzo auth required' 'test@test.blah'")


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.set_file_contents')
    def test_save_tokens(self, mock_set_file_contents, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.token_file = '/tmp/blah'
        api.access_token = 'access token 123'
        api.access_token_expiry = 'access_token_expiry 123'
        api.refresh_token = 'refresh_token 123'

        api.save_tokens()

        mock_set_file_contents.assert_called_with('/tmp/blah', '{"access_token": "access token 123", "expiry": "access_token_expiry 123", "refresh_token": "refresh_token 123"}')


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo.authentication.Authentication.__init__')
    def test_get_client(self, mock_init_auth, mock_init):
        mock_init.return_value = None
        mock_init_auth.return_value = None

        config = Config({
            'client_id': 'test',
            'client_secret': 'test',
            'redirect_url': 'test'
        })

        Config._instances[Config] = config

        api = MonzoAPI()
        api.access_token = 'access token'
        api.access_token_expiry = 'access token expiry'
        api.refresh_token = 'refresh token'
        api.get_client()

        mock_init_auth.assert_called_with(
            client_id='test',
            client_secret='test',
            redirect_url='test',
            access_token='access token',
            access_token_expiry='access token expiry',
            refresh_token='refresh token'
        )


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo.endpoints.account.Account.fetch')
    def test_account(self, mock_fetch, mock_init):
        mock_init.return_value = None
        mock_fetch.return_value = 'fetched account'

        api = MonzoAPI()
        api.client = 'client'

        resp = api.account(1234)

        self.assertEqual(resp, 'fetched account')

        mock_fetch.assert_called_with('client', account_id=1234)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.update_tokens')
    @patch('monzo.endpoints.account.Account.fetch')
    def test_accounts_return(self, mock_fetch, mock_update_tokens, mock_init):
        mock_init.return_value = None
        mock_fetch.return_value = ['returned accounts']

        api = MonzoAPI()
        api.client = 'client'

        resp = api.accounts()

        self.assertEqual(resp, ['returned accounts'])

        mock_update_tokens.assert_called()
        mock_fetch.assert_called_with('client')


    def raise_MonzoHTTPError(self, *args, **kwargs):
        raise MonzoHTTPError("error")

    def raise_MonzoAuthenticationError(self, *args, **kwargs):
        raise MonzoAuthenticationError("error")

    def raise_MonzoServerError(self, *args, **kwargs):
        raise MonzoServerError("error")


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo.endpoints.account.Account.fetch', new=raise_MonzoHTTPError)
    def test_accounts_http_error_noauth(self, mock_init):
        mock_init.return_value = None

        os.environ['NO_AUTH'] = '1'

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(Exception) as e:
            resp = api.accounts()

        self.assertIn("ExceptionInfo Exception('token expired')", str(e))


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo.endpoints.account.Account.fetch', new=raise_MonzoHTTPError)
    def test_accounts_http_error_without_noauth(self, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.accounts()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo.endpoints.account.Account.fetch', new=raise_MonzoAuthenticationError)
    def test_accounts_auth_error(self, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.accounts()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo.endpoints.account.Account.fetch', new=raise_MonzoServerError)
    @patch('time.sleep')
    def test_accounts_server_error(self, mock_sleep, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.accounts()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.save_tokens')
    def test_update_tokens_no_change(self, mock_save_tokens, mock_init):
        mock_init.return_value = None

        client = MagicMock()
        client.access_token = 'access token'
        client.access_token_expiry = 'access_token_expiry'
        client.refresh_token = 'refresh_token'

        api = MonzoAPI()
        api.access_token = 'access token'
        api.access_token_expiry = 'access_token_expiry'
        api.refresh_token = 'refresh_token'
        api.client = client

        api.update_tokens()

        mock_save_tokens.assert_not_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.save_tokens')
    def test_update_tokens_access_token_changed(self, mock_save_tokens, mock_init):
        mock_init.return_value = None

        client = MagicMock()
        client.access_token = 'access token'
        client.access_token_expiry = 'access_token_expiry'
        client.refresh_token = 'refresh_token'

        api = MonzoAPI()
        api.access_token = 'access token2'
        api.access_token_expiry = 'access_token_expiry'
        api.refresh_token = 'refresh_token'
        api.client = client

        api.update_tokens()

        mock_save_tokens.assert_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.save_tokens')
    def test_update_tokens_access_token_expiry_changed(self, mock_save_tokens, mock_init):
        mock_init.return_value = None

        client = MagicMock()
        client.access_token = 'access token'
        client.access_token_expiry = 'access_token_expiry'
        client.refresh_token = 'refresh_token'

        api = MonzoAPI()
        api.access_token = 'access token'
        api.access_token_expiry = 'access_token_expiry2'
        api.refresh_token = 'refresh_token'
        api.client = client

        api.update_tokens()

        mock_save_tokens.assert_called()


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.save_tokens')
    def test_update_tokens_refresh_token_changed(self, mock_save_tokens, mock_init):
        mock_init.return_value = None

        client = MagicMock()
        client.access_token = 'access token'
        client.access_token_expiry = 'access_token_expiry'
        client.refresh_token = 'refresh_token'

        api = MonzoAPI()
        api.access_token = 'access token'
        api.access_token_expiry = 'access_token_expiry'
        api.refresh_token = 'refresh_token2'
        api.client = client

        api.update_tokens()

        mock_save_tokens.assert_called()


    @patch('monzo.endpoints.transaction.Transaction.fetch')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('time.sleep')
    def test_transactions_return(self, mock_sleep, mock_init, mock_fetch):
        mock_init.return_value = None

        mock_fetch.return_value = ['transaction']

        api = MonzoAPI()
        api.client = 'client'
        api.transactions(123)

        args_0 = mock_fetch.call_args[0]

        self.assertEqual(args_0, ('client',))

        args_1 = mock_fetch.call_args[1]

        self.assertIn('account_id', args_1)
        self.assertIn('expand', args_1)
        self.assertIn('since', args_1)

        self.assertEqual(args_1['account_id'], 123)
        self.assertEqual(args_1['expand'], ['merchant'])
        self.assertIsInstance(args_1['since'], datetime.datetime)


    def raise_MonzoPermissionsError(self, *args, **kwargs):
        raise MonzoPermissionsError("error")

    @patch('monzo.endpoints.transaction.Transaction.fetch', new=raise_MonzoPermissionsError)
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('time.sleep')
    def test_transactions_permissions_error(self, mock_sleep, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(MonzoPermissionsError) as e:
            api.transactions(123)

        self.assertIn("ExceptionInfo MonzoPermissionsError('error')", str(e))


    def raise_Exception(self, *args, **kwargs):
        raise Exception("exception")

    @patch('monzo.endpoints.transaction.Transaction.fetch', new=raise_Exception)
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('time.sleep')
    def test_transactions_exception(self, mock_sleep, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(Exception) as e:
            api.transactions(123)

        self.assertIn("ExceptionInfo Exception('exception')", str(e))


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo.endpoints.pot.Pot.fetch', new=raise_MonzoHTTPError)
    def test_pots_http_error_noauth(self, mock_init):
        mock_init.return_value = None

        os.environ['NO_AUTH'] = '1'

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(Exception) as e:
            api.pots(account_id=123)

        self.assertIn("ExceptionInfo Exception('token expired')", str(e))


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch', new=raise_MonzoHTTPError)
    def test_pots_http_error_without_noauth(self, mock_get_client, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.pots(account_id=123)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch', new=raise_MonzoAuthenticationError)
    def test_pots_auth_error(self, mock_get_client, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.pots(account_id=123)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.authenticate')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch', new=raise_MonzoServerError)
    @patch('time.sleep')
    def test_pots_server_error(self, mock_sleep, mock_get_client, mock_auth, mock_init):
        mock_init.return_value = None

        api = MonzoAPI()
        api.client = 'client'

        with pytest.raises(SystemExit) as e:
            api.pots(account_id=123)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.load_tokens')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch_single')
    @patch('monzo.endpoints.pot.Pot.withdraw')
    def test_withdraw_from_pot_success(self, mock_withdraw, mock_fetch_single, mock_get_client, mock_load_tokens, mock_init):
        mock_init.return_value = None
        mock_get_client.return_value = 'client'

        pot = Pot({
            'pot_id': 324142
        })

        mock_fetch_single.return_value = pot

        api = MonzoAPI()

        with freeze_time("2024-01-01"):
            resp = api.withdraw_from_pot(123, pot, 10010)

        self.assertEqual(resp, True)

        mock_load_tokens.assert_called()
        mock_get_client.assert_called()
        mock_fetch_single.assert_called_with('client', account_id=123, pot_id=324142)

        mock_withdraw.assert_called_with('client', pot=pot, account_id=123, amount=1001000, dedupe_id='324142_2024010100')


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.load_tokens')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch_single')
    @patch('monzo.endpoints.pot.Pot.withdraw', new=raise_Exception)
    @patch('time.sleep')
    def test_withdraw_from_pot_exception(self, mock_sleep, mock_fetch_single, mock_get_client, mock_load_tokens, mock_init):
        mock_init.return_value = None
        mock_get_client.return_value = 'client'

        pot = Pot({
            'pot_id': 324142
        })

        mock_fetch_single.return_value = pot

        api = MonzoAPI()

        with freeze_time("2024-01-01"):
            resp = api.withdraw_from_pot(123, pot, 10010)

        self.assertEqual(resp, False)

        mock_load_tokens.assert_called()
        mock_get_client.assert_called()
        mock_fetch_single.assert_called_with('client', account_id=123, pot_id=324142)


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.load_tokens')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch_single')
    @patch('monzo.endpoints.pot.Pot.deposit')
    def test_deposit_to_pot_success(self, mock_withdraw, mock_fetch_single, mock_get_client, mock_load_tokens, mock_init):
        mock_init.return_value = None
        mock_get_client.return_value = 'client'

        pot = Pot({
            'pot_id': 324142
        })

        mock_fetch_single.return_value = pot

        api = MonzoAPI()

        with freeze_time("2024-01-01"):
            resp = api.deposit_to_pot(123, pot, 10010)

        self.assertEqual(resp, True)

        mock_load_tokens.assert_called()
        mock_get_client.assert_called()
        mock_fetch_single.assert_called_with('client', account_id=123, pot_id=324142)

        mock_withdraw.assert_called_with('client', pot=pot, account_id=123, amount=1001000, dedupe_id='324142_2024010100')


    @patch('monzo_utils.lib.monzo_api.MonzoAPI.__init__')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.load_tokens')
    @patch('monzo_utils.lib.monzo_api.MonzoAPI.get_client')
    @patch('monzo.endpoints.pot.Pot.fetch_single')
    @patch('monzo.endpoints.pot.Pot.deposit', new=raise_Exception)
    @patch('time.sleep')
    def test_deposit_to_pot_exception(self, mock_sleep, mock_fetch_single, mock_get_client, mock_load_tokens, mock_init):
        mock_init.return_value = None
        mock_get_client.return_value = 'client'

        pot = Pot({
            'pot_id': 324142
        })

        mock_fetch_single.return_value = pot

        api = MonzoAPI()

        with freeze_time("2024-01-01"):
            resp = api.deposit_to_pot(123, pot, 10010)

        self.assertEqual(resp, False)

        mock_load_tokens.assert_called()
        mock_get_client.assert_called()
        mock_fetch_single.assert_called_with('client', account_id=123, pot_id=324142)
