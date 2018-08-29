from utility import todict
import requests
import json
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout


class WalletAPI:
    base_url = 'http://127.0.0.1:8999/v1/wallet/'
    base_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    @staticmethod
    def create(name):
        try:
            response = requests.post(url=WalletAPI.base_url + 'create', data=name, headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def unlock(self, name='default'):
        try:
            body = json.dumps([name, self.get_pw(name)])
            response = requests.post(url=WalletAPI.base_url + 'unlock', data=body, headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def lock(name='default'):
        try:
            response = requests.post(url=WalletAPI.base_url + 'lock', data=name, headers=WalletAPI.base_headers)
            if response.status_code == 200:
                response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def list_wallets():
        try:
            response = requests.post(url=WalletAPI.base_url + 'list_wallets', headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def list_keys(password, name='default'):
        try:
            body = json.dumps([name, password])
            response = requests.post(url=WalletAPI.base_url + 'list_keys', data=body, headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def get_public_keys():
        try:
            response = requests.post(url=WalletAPI.base_url + 'get_public_keys',
                                     headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def create_key(key_type="K1", name="default"):
        try:
            body = json.dumps([name, key_type])
            response = requests.post(url=WalletAPI.base_url + 'create_key', data=body, headers=WalletAPI.base_headers)
            if response.status_code == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def import_key(private_key, name='default'):
        try:
            body = json.dumps([name, private_key])
            response = requests.post(url=WalletAPI.base_url + 'import_key', data=body, headers=WalletAPI.base_headers)
            if response.body == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def set_timeout(time_out):
        try:
            response = requests.post(url=WalletAPI.base_url + 'set_timeout', data=time_out,
                                     headers=WalletAPI.base_headers)
            if response.body == 200:
                return response.json()
        except ConnectionError as e:
            raise e

    @staticmethod
    def sign_transaction(transaction, keys, chain_id=""):
        try:
            body = json.dumps([todict(transaction), keys, chain_id])
            response = requests.post(url=WalletAPI.base_url + 'sign_transaction', data=body,
                                     headers=WalletAPI.base_headers)
            if response.status_code == 201:
                return response.json()
        except ConnectionError as e:
            raise e
