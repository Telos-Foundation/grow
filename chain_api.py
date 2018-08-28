import json
import logging
from datetime import datetime
from datetime import timedelta
from simple_rest_client.api import API
from simple_rest_client.resource import Resource
from simple_rest_client.exceptions import ServerError
from simple_rest_client.exceptions import ClientConnectionError
from wallet_api import WalletAPI
from utility import todict
from http.client import RemoteDisconnected


class ChainResource(Resource):
    actions = {
        'get_info': {'method': 'POST', 'url': 'get_info'},
        'get_block': {'method': 'POST', 'url': 'get_block'},
        'get_block_header_state': {'method': 'POST', 'url': 'get_block_header_state'},
        'get_account': {'method': 'POST', 'url': 'get_account'},
        'get_abi': {'method': 'POST', 'url': 'get_abi'},
        'get_code': {'method': 'POST', 'url': 'get_code'},
        'get_raw_code_and_abi': {'method': 'POST', 'url': 'get_raw_code_and_abi'},
        'get_table_rows': {'method': 'POST', 'url': 'get_table_rows'},
        'get_currency_balance': {'method': 'POST', 'url': 'get_currency_balance'},
        'get_currency_stats': {'method': 'POST', 'url': 'get_currency_stats'},
        'get_required_keys': {'method': 'POST', 'url': 'get_required_keys'},
        'abi_json_to_bin': {'method': 'POST', 'url': 'abi_json_to_bin'},
        'abi_bin_to_json': {'method': 'POST', 'url': 'abi_bin_to_json'},
        'get_producers': {'method': 'POST', 'url': 'get_producers'},
        'push_block': {'method': 'POST', 'url': 'push_block'},
        'push_transaction': {'method': 'POST', 'url': 'push_transaction'},
        'push_transactions': {'method': 'POST', 'url': 'push_transactions'}
    }


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

        if self.ref_block_num != 0:
            self.ref_block_num = self.get_ref_block_num()

        if self.ref_block_prefix != 0:
            self.ref_block_prefix = self.get_ref_block_prefix(self.ref_block_num)

    def add_action(self, action):
        if not self.actions:
            self.actions = []
        self.actions.append(action)

    def get_ref_block_num(self):
        return ChainAPI.get_info()['head_block_num']

    def get_ref_block_prefix(self, block_num):
        return ChainAPI.get_block(block_num)['ref_block_prefix']

    # trans.send()


class AccountName:

    def __init__(self, name):
        self.account_name = name


class Authority:

    def __init__(self, actor, permission):
        """Authority is the account_name and permission name used to authorize an action"""
        self.actor = actor
        self.permission = permission

    # authority.exists()


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
    api = ''

    @staticmethod
    def configure(host):
        ChainAPI.api = API(
            api_root_url='%s/v1/chain' % host,
            params={},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=2,
            append_slash=False,
            json_encode_body=True,
        )
        ChainAPI.api.add_resource(resource_name='chain', resource_class=ChainResource)

    @staticmethod
    def get_currency_balance(account, code='eosio.token', symbol='TLOS'):
        try:
            body = {'code': code, 'account': account, 'symbol': symbol}
            response = ChainAPI.api.chain.get_currency_balance(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_currency_stats(account, symbol='TLOS'):
        try:
            body = {'code': 'eosio.token', 'account': account, 'symbol': symbol}
            response = ChainAPI.api.chain.get_currency_stats(body=body, params={}, headers={})
            if response.status_code == 200 and len(response.body) > 0:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_block_header_state(block_num):
        try:
            body = {'block_num_or_id': block_num}
            response = ChainAPI.api.chain.get_block_header_state(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_info():
        try:
            response = ChainAPI.api.chain.get_info(body={}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_block(block_num_or_id):
        try:
            body = {'block_num_or_id': block_num_or_id}
            response = ChainAPI.api.chain.get_block(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_abi(account_name):
        try:
            response = ChainAPI.api.chain.get_abi(body={'account_name': account_name}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_code(account_name):
        try:
            response = ChainAPI.api.chain.get_code(body={'account_name': account_name}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def abi_json_to_bin(action_data):
        try:
            response = ChainAPI.api.chain.abi_json_to_bin(body=action_data, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def abi_bin_to_json(bin_data):
        try:
            response = ChainAPI.api.chain.abi_bin_to_json(body=bin_data, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_raw_code_and_abi(account_name):
        try:
            response = ChainAPI.api.chain.get_raw_code_and_abi(body={'account_name': account_name}, params={},
                                                               headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_account(account_name):
        try:
            response = ChainAPI.api.chain.get_account(body={'account_name': account_name}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_table_rows(code, scope, table, output_json=True, limit=1000, lower_bound=0, upper_bound=-1):
        try:
            body = {'code': code, 'scope': scope, 'table': table, 'json': output_json, 'limit': limit,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound}
            response = ChainAPI.api.chain.get_table_rows(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_producers(limit=1000, lower_bound='', output_json=True):
        try:
            body = {'limit': limit, 'lower_bound': lower_bound, 'json': output_json}
            response = ChainAPI.api.chain.get_producers(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def get_required_keys(transaction, available_keys):
        try:
            body = {'transaction': todict(transaction), 'available_keys': available_keys, 'compression': 'none'}
            response = ChainAPI.api.chain.get_required_keys(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    # NOTE: Doesn't support context free actions
    @staticmethod
    def push_transaction(transaction):
        try:
            response = ChainAPI.api.chain.push_transactions(body=transaction, params={}, headers={})
            print(response)
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e
        except ClientConnectionError as e:
            print('remote disconnected')

    # TODO: Create exception handler


if __name__ == '__main__':
    ChainAPI.configure('http://127.0.0.1:8888')
    WalletAPI.configure()
    action_data = ActionData('eosio.token', 'transfer',
                             {'from': 'eosio', 'to': 'goodblockio1', 'quantity': '1000.0000 TLOS',
                              'memo': 'for testing or whatever'})
    action = action_data.get_action()
    action.add_authorization(Authority('eosio', 'active'))
    trans = Transaction()
    trans.add_action(action)
    keys = WalletAPI.get_public_keys()
    key_for_signing = ChainAPI.get_required_keys(trans, keys)
    signed_transaction = WalletAPI.sign_transaction(trans, key_for_signing['required_keys'])
    receipt = ChainAPI.push_transaction(signed_transaction)
    print(receipt)
