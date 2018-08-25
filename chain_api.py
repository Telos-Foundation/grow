import json
import os
import psutil
import logging
from simple_rest_client.api import API
from simple_rest_client.resource import Resource
from asset import Asset
from simple_rest_client.exceptions import ServerError
from shutil import rmtree
from time import sleep
from utility import join
from utility import start_background_proc
from utility import file_get_contents
from utility import log_file


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

    def __init__(self, ref_block_num, ref_block_prefix, expiration, actions):
        """Transaction"""
        self.ref_block_num = ref_block_num
        self.ref_block_prefix = ref_block_prefix
        self.expiration = expiration
        self.actions = actions


class Authority:

    def __init__(self, actor, permission):
        """Authority is the account_name and permission name used to authorize an action"""
        self.actor = actor
        self.permission = permission

class Action:

    def __init__(self, account, authorization, data):
        """Action is used in pushing transactions to the RPC API"""
        self.account = account #NOTE: Account is the contract is set on.
        self.authorization = authorization #NOTE: Authorization is the permission level used for the action
        self.data = data #NOTE: Data is the binargs received from abi_json_to_bin RPC


class ActionData:

    def __init__(self, code, action, args):
        """ActionData is used to get bin data from the RPC API"""
        self.code = code
        self.action = action
        self.args = args


class ChainAPI:

    def __init__(self, host):
        self.api = API(
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
        self.api.add_resource(resource_name='chain', resource_class=ChainResource)

    def get_currency_balance(self, account, symbol='TLOS'):
        try:
            body = {'code': 'eosio.token', 'account': account, 'symbol': symbol}
            response = self.api.chain.get_currency_balance(body=body, params={}, headers={})
            if response.status_code == 200 and len(response.body) > 0:
                return Asset.string_to_asset(response.body[0])
            return Asset(0, 'TTT')
        except ServerError as e:
            raise e

    def get_block_header_state(self, block_num):
        try:
            body = {'block_num_or_id': block_num}
            response = self.api.chain.get_block_header_state(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    def get_info(self):
        try:
            response = self.api.chain.get_info(body={}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    def get_block(self, block_num_or_id):
        try:
            body = {'block_num_or_id': block_num_or_id}
            response = self.api.chain.get_block(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    def abi_json_to_bin(self, action_data):
        try:
            response = self.api.chain.abi_json_to_bin(body=action_data, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    def abi_bin_to_json(self, bin_data):
        try:
            response = self.api.chain.abi_bin_to_json(body=bin_data, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e


if __name__ == '__main__':
    api = ChainAPI('http://64.38.144.179:8888')
    print(ActionData('eosio.token', 'transfer', { "from": "eosio", "to": "noprom", "quantity": "1.0000 EOS", "memo": "created by noprom" }).__dict__)
    #print(api.abi_bin_to_json({'code':'eosio.token','action':'transfer','binargs': '0000000000ea305500000000487a2b9d102700000000000004454f53000000001163726561746564206279206e6f70726f6d'}))
