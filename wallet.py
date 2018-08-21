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

        if forceRestart:
            self.reset()

        if not self.is_running():
            #print("Init start wallet function")
            self.start_wallet()

        if not self.exists() and os.path.isfile(teclos_dir):
            #print("Creating wallet because none exists")
            self.create()

    def exists(self):
        #print("wallet exists: " + str(self.wallet_exists('default')))
        #print("tkeosd is running: " + str(self.is_running()))
        return self.is_running() and self.wallet_exists('default')

    def is_running(self):
        #print("is_running()")
        try:
            pid = self.get_pid()
            #print('keosd pid: ' + str(pid))
            if pid != -1:
                return psutil.pid_exists(self.pid)
            return False
        except OSError as e:
            print(e)

    def get_pid(self):
        #print("get_pid()")
        path = join(self.wallet_state, 'keosd.pid')
        if os.path.isfile(path):
            pid = int(file_get_contents(path))
            self.pid = pid
            return pid

    def stop(self):
        try:
            pid = self.get_pid()
            if pid != -1 and self.is_running():
                p = psutil.Process(pid)
                p.terminate()
        except OSError as e:
            print(e)

    def __str__(self):
        info = {'name': self.name, 'pid': self.get_pid(), 'path': self.path}
        return json.dumps(info)

    def create(self):
        if not self.is_running():
            self.start_wallet()
        if not os.path.exists(self.wallet_state):
            os.makedirs(self.wallet_state)
        o = get_output(self.teclos_start + ' wallet create --to-console')
        f = open(join(self.wallet_state, 'wallet_pw.txt'), 'w')
        f.write(self.parse_pw(o))

    def unlock(self):
        if not self.exists():
            #print('No existing wallet, creating default wallet')
            self.create()
        elif self.is_locked():
            run(self.teclos_start + ' wallet unlock --password ' + self.get_pw())

    def lock(self):
        if not self.exists():
            print('No existing wallet, creating default wallet')
            self.create()
        elif not self.is_locked():
            run(self.teclos_start + ' wallet lock')

    def is_locked(self):
        try:
            o = get_output(self.teclos_start + ' wallet list')
            j = json.loads(o[o.index(':') + 2:len(o)])
            for wallet in j:
                if 'default' in wallet and '*' in wallet:
                    return False
            return True
        except ValueError as e:
            print(e)
        except OSError as e:
            print(e)

    def wallet_exists(self, wallet_name):
        try:
            o = get_output(self.teclos_start + ' wallet list')
            j = json.loads(o[o.index(':') + 2:len(o)])
            for wallet in j:
                if wallet_name in wallet:
                    print('wallet found: ' + wallet_name)
                    return True
            #print("wallet not found")
            return False
        except ValueError as e:
            print(e)
        except OSError as e:
            print(e)

    def get_keys(self):
        try:
            if self.is_locked():
                self.unlock()
            o = get_output(self.teclos_start + ' wallet private_keys --password %s' % self.get_pw())
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
        if self.is_locked():
            self.unlock()
        o = get_output(self.teclos_start + ' wallet private_keys --password %s' % self.get_pw())
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
        run(self.teclos_start + ' wallet import --private-key %s' % (private_key))

    def parse_pw(self, o):
        try:
            if (o != "" or o != None) and 'Error' not in o:
                r = o[o.index('"') + 1:len(o) - 2]
                return r
            else:
                print('unable to parse wallet password')
        except ValueError as e:
            print(e)

    def start_wallet(self):
        if self.is_running():
            self.stop()
        if not os.path.isdir(self.wallet_state):
            os.makedirs(self.wallet_state)
        start_background_proc(
            self.keosd_dir + ' --unlock-timeout %d --http-server-address 127.0.0.1:8999' % (self.unlockTimeout),
            log_file(join(self.wallet_state, 'stderr.txt')), join(self.wallet_state, 'keosd.pid'))
        sleep(.4)

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

    def kill_daemon(self):
        try:
            for proc in psutil.process_iter():
                if proc.name() == 'keosd':
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
