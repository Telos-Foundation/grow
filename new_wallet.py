import json
import os
import psutil
import logging
from simple_rest_client.api import API
from simple_rest_client.resource import Resource
from simple_rest_client.exceptions import ServerError
from shutil import rmtree
from time import sleep
from utility import join
from utility import start_background_proc
from utility import file_get_contents
from utility import log_file


class KeyPair:
    def __init__(self, public, private):
        self.public = public
        self.private = private

    def __str__(self):
        return json.dumps({'public': self.public, 'private': self.private})


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

class Wallet:

    def __init__(self, wallet_state, keosd_dir, unlockTimeout=120):
        self.wallet_state = wallet_state
        self.wallet_dir = join(os.path.expanduser('~'), 'telos-wallet')
        self.keosd_dir = keosd_dir
        self.unlockTimeout = unlockTimeout
        self.api = API(
            api_root_url='http://127.0.0.1:8999/v1/wallet',
            params={},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=2,
            append_slash=False,
            json_encode_body=True,
        )
        self.api.add_resource(resource_name='wallet', resource_class=WalletResource)
        self.pid = -1
        if not self.is_running():
            self.start_wallet()

        if not self.wallet_exists('default'):
            self.create('default')

    def is_running(self):
        try:
            p = psutil.Process(self.get_pid())
            if p.is_running():
                return True
            return False
        except psutil.ZombieProcess:
            return False
        except psutil.NoSuchProcess:
            return False

    def get_pid(self):
        path = join(self.wallet_state, 'keosd.pid')
        if os.path.isfile(path):
            pid = int(file_get_contents(path))
            self.pid = pid
            return pid
        return 0

    def stop(self):
        try:
            p = psutil.Process(self.get_pid())
            if p.is_running() and p.name() == 'tkeosd':
                p.kill()
        except OSError as e:
            print(e)

    def update_pid(self, pid):
        path = join(self.wallet_state, 'keosd.pid')
        if os.path.isfile(path):
            os.rmdir()
            with open(path, 'w') as pid_file:
                pid_file.write(pid)
            return pid
        return 0

    def __str__(self):
        info = {'name': self.name, 'pid': self.get_pid(), 'path': self.path}
        return json.dumps(info)

    def create(self, name):
        try:
            response = self.api.wallet.create(body=name, params={}, headers={})
            self.set_pw(name, response.body)
        except ServerError as e:
            raise e

    def unlock(self, name='default'):
        try:
            if not self.is_locked():
                print('Wallet: %s is already unlocked' % name)
                return
            body = [name, self.get_pw(name)]
            response = self.api.wallet.unlock(body=body, params={}, headers={})
            if response.status_code == 200:
                print('Wallet: %s is unlocked' % name)
                return True
            return False
        except ServerError as e:
            raise e

    def lock(self, name='default'):
        try:
            response = self.api.wallet.lock(body=name, params={}, headers={})
            if response.status_code == 200:
                print('Wallet: %s locked' % name)
                return True
            return False
        except ServerError as e:
            raise e

    def list_wallets(self):
        try:
            response = self.api.wallet.list_wallets(body={}, params={}, headers={})
            return response.body
        except ServerError as e:
            raise e

    def is_locked(self, name='default'):
        wallets = self.list_wallets()
        for wallet in wallets:
            if name in wallet and '*' in wallet:
                return False
            elif name in wallet:
                return True
        #raise no wallet with that name exception

    def wallet_exists(self, name='default'):
        wallets = self.list_wallets()
        for wallet in wallets:
            if name in wallet:
                return True
        print('no wallet found: ' + name)
        return False

    def to_keypair(self, array):
        return KeyPair(array[0], array[1])

    def get_keys(self, name='default'):
        if self.is_locked():
            self.unlock()
        body = [name, self.get_pw(name)]
        response = self.api.wallet.list_keys(body=body, params={}, headers={})
        return response.body

    def get_keyarray(self, public_key,  name='default'):
        keys = self.get_keys(name)
        for pair in keys:
            if pair[0] == public_key:
                return self.to_keypair(pair)
        return None

    def contains_key(self, key, name='default'):
        keys = self.get_keys(name)
        for pair in keys:
            for key_in_pair in pair:
                if key_in_pair == key:
                    return True
        return False

    def create_import(self):
        return self.create_key()

    def create_key(self, key_type="K1", name="default"):
        try:
            if self.is_locked():
                self.unlock()
            body = [name, key_type]
            response = self.api.wallet.create_key(body=body, params={}, headers={})
            return self.get_keyarray(response.body, name)
        except ServerError as e:
            raise e

    def import_key(self, private_key, name='default'):
        try:
            body = [name, private_key]
            response = self.api.wallet.import_key(body=body, params={}, headers={})
            return response.status_code == 200
        except ServerError as e:
            raise e

    def start_wallet(self):
        if not os.path.isdir(self.wallet_state):
            os.makedirs(self.wallet_state)
        start_background_proc(
            self.keosd_dir + ' --unlock-timeout %d --http-server-address 127.0.0.1:8999' % (self.unlockTimeout),
            log_file(join(self.wallet_state, 'stderr.txt')), join(self.wallet_state, 'keosd.pid'))
        sleep(.4)

    def get_pw(self, name):
        try:
            p = join(self.wallet_state, "wallet_pw.json")
            if os.path.isfile(p):
                j = json.loads(file_get_contents(p))
                if name in j:
                    return j[name]
            return None
        except Exception as e:
            print(e)

    def set_pw(self, name, pw):
        try:
            p = join(self.wallet_state, "wallet_pw.json")
            j = {}
            if not os.path.isdir(self.wallet_state):
                os.mkdir(self.wallet_state)
            if os.path.isfile(p):
                j = json.loads(file_get_contents(p))
            j[name] = pw
            with open(p, 'w') as pw_file:
                pw_file.write(json.dumps(j))
        except Exception as e:
            print(e)

    def kill_daemon(self):
        try:
            for proc in psutil.process_iter():
                if proc.name() == 'tkeosd':
                    proc.kill()
        except:
            pass

    def reset(self):
        self.stop()
        self.kill_daemon()
        if os.path.isdir(self.wallet_state):
            rmtree(self.wallet_state)
        if os.path.isdir(self.wallet_dir):
            rmtree(self.wallet_dir)

    def recover(self):
        if not self.is_running():
            self.start_wallet()
        if not self.wallet_exists('default'):
            self.create('default')


if __name__ == '__main__':
    print('starting test')
    wallet = Wallet('wallet', '/Users/hotmdev4/Desktop/telos/build/programs/tkeosd/tkeosd')
    print(wallet.create('default'))
