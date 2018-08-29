import json
import logging
from datetime import datetime
from datetime import timedelta
from wallet_api import WalletAPI
from utility import todict
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout


class Transaction:
    def __init__(self, *initial_data, **kwargs):
        """Transaction"""
        self.expiration = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        self.ref_block_num = 0
        self.ref_block_prefix = 0
        self.max_net_usage_words = 0
        self.max_cpu_usage_ms = 0
        self.delay_sec = 0
        self.context_free_actions = []
        self.context_free_data = []
        self.actions = []
        self.signatures = []

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.ref_block_num == 0:
            self.ref_block_num = self.get_ref_block_num()

        if self.ref_block_prefix == 0:
            self.ref_block_prefix = self.get_ref_block_prefix(self.ref_block_num)

    def add_action(self, action):
        if not self.actions:
            self.actions = []
        self.actions.append(action)

    def get_ref_block_num(self):
        return ChainAPI.get_info()['head_block_num']

    def get_ref_block_prefix(self, block_num):
        return ChainAPI.get_block(block_num)['ref_block_prefix']

    def send(self):
        """Send transaction"""


class AccountName:

    def __init__(self, name):
        self.account_name = name

    def exists(self):
        """Checks to see if an account exists"""
        r = ChainAPI.get_account(self.account_name)
        if r:
            return r['account_name'] is self.account_name
        return False


class Authority:

    def __init__(self, actor, permission):
        """Authority is the account_name and permission name used to authorize an action"""
        self.actor = actor
        self.permission = permission

    def exists(self):
        r = ChainAPI.get_account(self.account_name)
        if r:
            for permission in r['permissions']:
                if permission is self.permission:
                    return True
        return False


class Action:

    def __init__(self, account, action_name, data):
        """Action is used in pushing transactions to the RPC API"""
        self.account = account  # NOTE: code, is the account_name the contract is set on.
        self.name = action_name
        self.authorization = []  # NOTE: Authorization is the permission_level used for the action
        self.data = data  # NOTE: Data is the binargs received from abi_json_to_bin RPC

    def add_authorization(self, authority):
        # TODO: Validate given authority s
        self.authorization.append(authority)

    # action.validate()


class ActionData:

    def __init__(self, code, action, args):
        """ActionData is used to get bin data from the RPC API"""
        self.code = code
        self.action = action
        self.args = args

    def get_action(self):
        binargs = ChainAPI.abi_json_to_bin(self.__dict__)
        return Action(self.code, self.action, binargs['binargs'])


class ChainAPI:
    base_url = ''
    base_headers = headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    @staticmethod
    def configure(host):
        ChainAPI.base_url = '%s/v1/chain/' % host

    @staticmethod
    def get_currency_balance(account, code='eosio.token', symbol='TLOS'):
        try:
            body = json.dumps({'code': code, 'account': account, 'symbol': symbol})
            response = requests.post(url=ChainAPI.base_url + 'get_currency_balance', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_currency_stats(account, symbol='TLOS'):
        try:
            body = json.dumps({'code': 'eosio.token', 'account': account, 'symbol': symbol})
            response = requests.post(url=ChainAPI.base_url + 'get_currency_stats', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200 and len(response.body) > 0:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_block_header_state(block_num):
        try:
            body = json.dumps({'block_num_or_id': block_num})
            response = requests.post(url=ChainAPI.base_url + 'get_block_header_state', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_info():
        try:
            response = requests.post(url=ChainAPI.base_url + 'get_info', headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_block(block_num_or_id):
        try:
            body = json.dumps({'block_num_or_id': block_num_or_id})
            response = requests.post(url=ChainAPI.base_url + 'get_block', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(response.json())
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_abi(account_name):
        try:
            body = json.dumps({'account_name': account_name})
            response = requests.post(url=ChainAPI.base_url + 'get_abi', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_code(account_name):
        try:
            body = json.dumps({'account_name': account_name})
            response = requests.post(url=ChainAPI.base_url + 'get_code', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def abi_json_to_bin(action_data):
        try:
            print(action_data)
            response = requests.post(url=ChainAPI.base_url + 'abi_json_to_bin', data=json.dumps(action_data),
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def abi_bin_to_json(bin_data):
        try:
            response = requests.post(url=ChainAPI.base_url + 'abi_bin_to_json', data=bin_data,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_raw_code_and_abi(account_name):
        try:
            body = json.dumps({'account_name': account_name})
            response = requests.post(url=ChainAPI.base_url + 'get_raw_code_and_abi', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_account(account_name):
        try:
            body = json.dumps({'account_name': account_name})
            response = requests.post(url=ChainAPI.base_url + 'get_account', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_table_rows(code, scope, table, output_json=True, limit=1000, lower_bound=0, upper_bound=-1):
        try:
            body = json.dumps({'code': code, 'scope': scope, 'table': table, 'json': output_json, 'limit': limit,
                               'lower_bound': lower_bound,
                               'upper_bound': upper_bound})
            response = requests.post(url=ChainAPI.base_url + 'get_table_rows', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_producers(limit=1000, lower_bound='', output_json=True):
        try:
            body = json.dumps({'limit': limit, 'lower_bound': lower_bound, 'json': output_json})
            response = requests.post(url=ChainAPI.base_url + 'get_producers', data=body, headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_required_keys(transaction, available_keys):
        try:
            body = json.dumps({'transaction': todict(transaction), 'available_keys': available_keys})
            response = requests.post(url=ChainAPI.base_url + 'get_required_keys', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def push_transaction(transaction):
        try:
            body = json.dumps(
                {'transaction': transaction, 'signatures': transaction['signatures'], 'compression': 'none'})
            response = requests.post(url=ChainAPI.base_url + 'push_transaction', data=body,
                                     headers=ChainAPI.base_headers)
            if response.status_code == 200:
                return response.json()
            else:
                return response.json()
        except ConnectionError as e:
            raise e


if __name__ == '__main__':
    print('Attempting to send transaction')
    ChainAPI.configure('http://127.0.0.1:8888')
    action_data = ActionData('eosio.token', 'transfer',
                             {'from': 'eosio', 'to': 'goodblockio1', 'quantity': '1000.0000 TLOS',
                              'memo': 'for testing or whatever'})

    action = action_data.get_action()
    action.add_authorization(Authority('eosio', 'active'))
    trans = Transaction(actions=[action])
    key_for_signing = ChainAPI.get_required_keys(trans, WalletAPI.get_public_keys())
    signed_transaction = WalletAPI.sign_transaction(trans, key_for_signing['required_keys'],
                                                    ChainAPI.get_info()['chain_id'])
    receipt = ChainAPI.push_transaction(signed_transaction)
    print(receipt)
