import csv
import json
from utility import run
from utility import id_generator
from utility import run_retry
from asset import Asset
from random import randint
from wallet import KeyPair
from bootstrapper import BootStrapper


class Account:
    def __init__(self, name, keypair):
        self.name = name
        self.keypair = keypair

    def __str__(self):
        return json.dumps({'name': self.name, 'pair': str(self.keypair)})


class AccountFactory:

    def __init__(self, wallet, teclos):
        self.wallet = wallet
        self.teclos = teclos
        self.host_address = 'http://localhost:8888'

    def set_host_address(self, address):
        self.host_address = address

    def pre_sys_create(self, a):
        self.wallet.import_key(a.keypair.private)
        run(self.teclos + ' --url %s create account eosio %s %s' % (self.host_address, a.name, a.keypair.public))

    def post_sys_create(self, a, net, cpu, ram, creator='eosio'):
        net = Asset(net)
        cpu = Asset(cpu)
        ram = Asset(ram)
        cmd = self.teclos + ' --url %s system newaccount %s --transfer %s %s --stake-net \"%s\" --stake-cpu \"%s\" --buy-ram \"%s\"'
        run_retry(cmd % (self.host_address, creator, a.name, a.keypair.public, net, cpu, ram))


    #TODO: make sure the account name meetings TELOS normalized requirements
    def get_acc_obj(self, account_name, import_key=False):
        if import_key:
            pair = self.wallet.create_import()
        else:
            pair = self.wallet.create_key()
        a = Account(account_name, pair)
        return a

    def create_accounts_from_csv(self, path_to_csv):
        try:
            with open(path_to_csv, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    amt = float(row['token_amt'])
                    liquid = 0.1000 if amt < 3.0000 else 10.0000 if amt > 11.000 else 2.0000 
                    remainder = amt - liquid
                    cpu = remainder / 2
                    net = remainder - cpu
                    a = Account(row['name'], KeyPair(row['telos_key'], ''))
                    if cpu + net + liquid == amt:
                        print('name: %s, amt: %s, liquid: %s, cpu: %s, net: %s, total: %s' % (row['name'], format(amt, '.4f'), liquid, cpu, net, format((cpu + net + liquid), '.4f')))
                    else:
                        print (cpu + net + liquid) + ' != '
        except Exception as e:
            print(e)    

    def create_system_accounts(self, account_names):
        accounts = []
        self.wallet.unlock()
        for name in account_names:
            a = self.get_acc_obj(name)
            self.pre_sys_create(a)
            accounts.append(a)
        return accounts

    def create_random_accounts(self, num_accounts, min, max, base = "acctname"):
        accounts = []
        for _ in range(num_accounts):
            a = self.get_acc_obj(base + id_generator())
            self.post_sys_create(a, Asset(randint(min, max)), Asset(randint(min, max)), Asset(randint(min, max)))
            accounts.append(a)
        return accounts