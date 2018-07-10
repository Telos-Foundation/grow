import os
import sys
import json
from time import sleep
from tlos_utility import run
from tlos_utility import get_output
from tlos_utility import background
from tlos_utility import start_background_proc
from tlos_utility import log_file

class tlos_wallet:
    wallet_dir = ""
    teclos_dir = ""
    eos_dir = ""
    keosd_dir = ""
    wallet_address = 'http://127.0.0.1:8900'
    teclos_start = ""
    unlockTimeout = 0

    def __init__(self, wallet_dir, teclos_dir, eos_dir, keosd_dir, unlockTimeout = 120):
        self.wallet_dir = wallet_dir
        self.teclos_dir = teclos_dir
        self.eos_dir = eos_dir
        self.keosd_dir = keosd_dir
        self.teclos_start = "%s --wallet-url %s" % (teclos_dir, self.wallet_address)
        self.unlockTimeout = unlockTimeout
        if not self.exists() and os.path.isfile(teclos_dir):
            self.create()

    def exists(self):
        return os.path.isdir(self.wallet_dir) and os.path.isdir(os.path.join(os.path.expanduser('~'), 'telos-wallet'))

    def create(self):
        print "creating wallet"
        self.start_wallet()
        if not os.path.exists(self.wallet_dir):
            os.makedirs(self.wallet_dir)
        o = get_output(self.teclos_start + ' wallet create')
        f = open(os.path.join(self.wallet_dir, 'wallet_pw.txt'), 'w')
        f.write(self.parse_pw(o))

    def unlock(self):
        if not self.exists():
            print 'No existing wallet, creating default wallet'
            self.create()
        elif self.is_locked():
            run(self.teclos_start + ' wallet unlock --password ' + self.get_pw())
            

    def lock(self):
        if not self.exists():
            print 'No existing wallet, creating default wallet'
            self.create()
        elif not self.is_locked():
            run(self.teclos_start + ' wallet lock')

    def is_locked(self):
        try:
            o = get_output(self.teclos_start + ' wallet list')
            j = o[o.index(':') + 2:len(o)]
            for wallet in j:
                if 'default' in wallet and '*' in wallet:
                    return True
            return False
        except ValueError as e:
            print ('Error occured while attempting to parse wallet password! Message: %s' % e.message)
        except OSError as e:
            print ('Error occured while attempting to get file! %s' % e.message)

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
            print ('Error occured while attempting to get file! %s' % e.message)
        

    def contains_key(self, key):
        if self.is_locked():
            self.unlock()
        o = get_output(self.teclos_start + ' wallet private_keys --password %s' % self.get_pw())
        j = json.loads(o)
        for keypair in j:
            if key == keypair[0] or key == keypair[1]:
                return True
        return False

    def create_key(self):
        try:
            o =  filter(None, get_output(self.teclos_dir + ' create key').split("\n"))
            private = o[0][o[0].index(':') + 2:len(o[0])]
            public = o[1][o[1].index(':') + 2:len(o[1])]
            return { "private" : private, "public" : public }
        except ValueError as e:
            print ('Error occured while attempting to parse wallet password! Message: %s' % e.message)

    def import_key(self, private_key):
        run(self.teclos_start + ' wallet import %s' % (private_key))

    def parse_pw(self, o):
        try:
            if (o != "" or o != None) and 'Error' not in o:
                r = o[o.index('"') + 1:len(o) - 2]
                return r
            else: 
                print 'unable to parse wallet password'
        except Exception as identifier:
            print 'An error occurred while parsing password. Do you have a wallet?'
            print identifier.message
            sys.exit(1)

    def start_wallet(self):
        os.makedirs(self.wallet_dir)
        start_background_proc(self.keosd_dir + ' --unlock-timeout %d --http-server-address 127.0.0.1:8900' % (self.unlockTimeout), log_file(os.path.join(self.wallet_dir, 'stderr.txt')), os.path.join(self.wallet_dir, 'keosd.pid'))
        sleep(3.0)

    def get_pw(self):
        try:
            p = os.path.join(self.wallet_dir, "wallet_pw.txt")
            if os.path.exists(p):
                f = open(p, 'r')
                return f.readline()
            else:
                print "wallet password does not exist"
        except Exception as identifier:
            print 'An error occurred while attempting to get wallet password from ./wallet/wallet_pw.txt'
            print identifier.message
            sys.exit(1)