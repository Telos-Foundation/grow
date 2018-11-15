import json
import os
import psutil
from shutil import rmtree
from time import sleep
from utility import join
from utility import run
from utility import get_output
from utility import start_background_proc
from utility import file_get_contents
from utility import log_file
from utility import did_run


class KeyPair:
    def __init__(self, public, private):
        self.public = public
        self.private = private

    def __str__(self):
        return json.dumps({'public': self.public, 'private': self.private})


class Wallet:

    def __init__(self, wallet_state, teclos_dir, telos_dir, keosd_dir, unlockTimeout=120, forceRestart = False):
        self.wallet_state = wallet_state
        self.wallet_dir = join(os.path.expanduser('~'), 'telos-wallet')
        self.teclos_dir = teclos_dir
        self.telos_dir = telos_dir
        self.keosd_dir = keosd_dir
        self.wallet_address = 'http://127.0.0.1:8999'
        self.teclos_start = '%s --wallet-url %s' % (teclos_dir, self.wallet_address)
        self.unlockTimeout = unlockTimeout
        self.pid = -1

        if not self.open():
            self.create()

    def exists(self):
        return self.wallet_exists('default')

    def stop(self):
        run('pkill -9 keosd')

    def __str__(self):
        info = {'name': self.name, 'pid': self.get_pid(), 'path': self.path}
        return json.dumps(info)

    def create(self):
        if not os.path.exists(self.wallet_state):
            os.makedirs(self.wallet_state)
        run(self.teclos_dir + ' wallet create --file ' + join(self.wallet_state, 'wallet_pw.txt'))

    def open(self):
        return did_run('{} wallet open'.format(self.teclos_dir))

    def unlock(self):
        did_run(self.teclos_dir + ' wallet unlock --password ' + self.get_pw())

    def lock(self):
        did_run(self.teclos_dir + ' wallet lock')

    def get_keys(self):
        try:
            self.unlock()
            o = get_output(self.teclos_dir + ' wallet private_keys --password %s' % self.get_pw())
            j = json.loads(o)
            output = []
            for keypair in j:
                d = {}
                d['public'] = keypair[0]
                d['private'] = keypair[1]
                output.append(d)
            return output
        except OSError as e:
            print(e)

    def contains_key(self, key):
        self.unlock()
        o = get_output(self.teclos_dir + ' wallet private_keys --password %s' % self.get_pw())
        j = json.loads(o)
        for keypair in j:
            if key == keypair[0] or key == keypair[1]:
                return True
        return False

    def create_import(self):
        pair = self.create_key()
        self.import_key(pair.private)
        return pair

    def create_key(self):
        try:
            o = get_output(self.teclos_dir + ' create key --to-console').split("\n")
            private = o[0][o[0].index(':') + 2:len(o[0])]
            public = o[1][o[1].index(':') + 2:len(o[1])]
            return KeyPair(public, private)
        except ValueError as e:
            print(e)

    def import_key(self, private_key):
        run(self.teclos_dir + ' wallet import --private-key %s' % (private_key))

    def parse_pw(self, o):
        try:
            if (o != "" or o != None) and 'Error' not in o:
                r = o[o.index('"') + 1:len(o) - 2]
                return r
            else:
                print('unable to parse wallet password')
        except ValueError as e:
            print(e)

    def get_pw(self):
        try:
            p = join(self.wallet_state, "wallet_pw.txt")
            if os.path.exists(p):
                f = open(p, 'r')
                return f.readline()
            else:
                print('wallet password does not exist')
        except Exception as e:
            print(e)

    def reset(self):
        self.stop()
        if os.path.isdir(self.wallet_state):
            rmtree(self.wallet_state)
        if os.path.isdir(self.wallet_dir):
            rmtree(self.wallet_dir)
