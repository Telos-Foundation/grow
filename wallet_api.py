from simple_rest_client.api import API
from simple_rest_client.resource import Resource
from simple_rest_client.exceptions import ServerError


class WalletResource(Resource):
    actions = {
        'open': {'method': 'POST', 'url': 'open'},
        'create': {'method': 'POST', 'url': 'create'},
        'lock': {'method': 'POST', 'url': 'lock'},
        'lock_all': {'method': 'POST', 'url': 'lock_all'},
        'unlock': {'method': 'POST', 'url': 'unlock'},
        'import_key': {'method': 'POST', 'url': 'import_key'},
        'list_wallets': {'method': 'POST', 'url': 'list_wallets'},
        'list_keys': {'method': 'POST', 'url': 'list_keys'},
        'get_public_keys': {'method': 'POST', 'url': 'get_public_keys'},
        'set_timeout': {'method': 'POST', 'url': 'set_timeout'},
        'set_dir': {'method': 'POST', 'url': 'set_dir'},
        'set_eosio_key': {'method': 'POST', 'url': 'set_eosio_key'},
        'create_key': {'method': 'POST', 'url': 'create_key'}
    }


class WalletAPI:
    api = ''

    @staticmethod
    def configure():
        WalletAPI.api = API(
            api_root_url='http://127.0.0.1:8999/v1/wallet',
            params={},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=2,
            append_slash=False,
            json_encode_body=True
        )
        WalletAPI.api.add_resource(resource_name='wallet', resource_class=WalletResource)

    @staticmethod
    def create(name):
        try:
            response = WalletAPI.api.wallet.create(body=name, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def unlock(self, name='default'):
        try:
            body = [name, self.get_pw(name)]
            response = WalletAPI.api.wallet.unlock(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def lock(name='default'):
        try:
            response = WalletAPI.api.wallet.lock(body=name, params={}, headers={})
            if response.status_code == 200:
                response.body
        except ServerError as e:
            raise e

    @staticmethod
    def list_wallets():
        try:
            response = WalletAPI.api.wallet.list_wallets(body={}, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def list_keys(password, name='default'):
        body = [name, password]
        response = WalletAPI.api.wallet.list_keys(body=body, params={}, headers={})
        if response.status_code == 200:
            return response.body

    @staticmethod
    def create_key(key_type="K1", name="default"):
        try:
            body = [name, key_type]
            response = WalletAPI.api.wallet.create_key(body=body, params={}, headers={})
            if response.status_code == 200:
                return response.body
        except ServerError as e:
            raise e

    @staticmethod
    def import_key(private_key, name='default'):
        try:
            body = [name, private_key]
            response = WalletAPI.api.wallet.import_key(body=body, params={}, headers={})
            if response.body == 200:
                return response.body
        except ServerError as e:
            raise e