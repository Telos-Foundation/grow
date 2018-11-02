import os
from utility import jsonArg
from utility import run
from utility import run_retry
from utility import join
from random import randint
from time import sleep
from asset import Asset


class BootStrapper:
    systemAccounts = [
      "eosio.bpay",
      "eosio.msig",
      "eosio.names",
      "eosio.ram",
      "eosio.ramfee",
      "eosio.saving",
      "eosio.stake",
      "eosio.token",
      "eosio.vpay"
      "eosio.amend",
      "eosio.trail"
    ]

    systemContracts = [
        {
          "owner": "eosio.token",
          "name": "eosio.token"
        },
        {
          "owner": "eosio.msig",
          "name": "eosio.msig"
        }
    ]

    token_supply = 10000000000
    token_issue = 190473249

    def __init__(self, telos, teclos, host_address, account_factory):
        self.telos_dir = telos
        self.teclos_dir = teclos
        self.host_address = host_address
        self.contracts = 'build/contracts'
        self.account_factory = account_factory

    def set_host_address(self, address):
        self.host_address = address

    def boot_strap_node(self, address):
        self.set_host_address(address)
        self.account_factory.set_host_address(address)
        #TODO: Make sure full node has eosio root key in wallet
        self.account_factory.create_system_accounts(self.systemAccounts)
        self.set_system_contracts(self.systemContracts)
        self.issue_token(self.token_supply, self.token_issue)
        system_contract = join(join(self.telos_dir, self.contracts), 'eosio.system')
        run(self.teclos_dir + ' --url %s set contract eosio %s -p eosio' % (self.host_address, system_contract))
        run(self.teclos_dir + ' --url %s push action eosio setpriv \'[\"eosio.msig\", 1]\' -p eosio@active' % self.host_address)
        for i in range(97, 123):
            account = self.account_factory.get_acc_obj('testaccount' + chr(i), True)
            self.account_factory.post_sys_create(account, 50.0000, 50.0000, 100.0000)
            BootStrapper.transfer(self.host_address, 'eosio', account.name, Asset(300.0000), 'initial transfer')

    def create_fund_account(self):
        a = self.account_factory.get_acc_obj('telosfundacc')
        self.account_factory.post_sys_create(a, (self.token_issue * 0.15) / 2,
                                             (self.token_issue * 0.15) / 2, 1000.0000)
        BootStrapper.transfer(self.host_address, 'eosio', a.name, Asset(1000.0000),
                 "Sending 15 percent stake and enough money to create new accounts")

    def set_system_contracts(self, contract_names):
        try:
            for contract in contract_names:
                name = contract['name']
                path = join(os.path.abspath(self.telos_dir), join(self.contracts, name))
                self.set_contract(contract['owner'], path)
        except IOError as e:
            print(e)

    def set_contract(self, account_name, path, p=""):
        print(self.host_address)
        cmd = self.teclos_dir + ' --url %s set contract %s %s'
        if p != "":
            cmd += ' -p %s' % p
        run_retry(cmd % (self.host_address, account_name, path))

    def push_action(self, target, action_name, json):
        run_retry(self.teclos_dir + ' --url %s push action %s %s %s' % (self.host_address, target, action_name, json))

    def vote_producers(self, a_accounts, b_accounts, minimum=10, maximum=30):
        for a in a_accounts:
            cmd = self.teclos_dir + ' --url %s system voteproducer prods ' + a.name + ' '
            i = 0
            for t in b_accounts:
                if a.name != t.name and i < randint(minimum, maximum):
                    cmd += t.name + " "
                    i = i + 1
            run_retry(cmd % self.host_address)

    def self_vote_producers(self, a_accounts, num_accounts=10000000):
        i = 0
        for a in a_accounts:
            if i < num_accounts:
                cmd = self.teclos_dir + ' --url %s system voteproducer approve ' + a.name + ' ' + a.name
                run_retry(cmd % self.host_address)
                i = i + 1

    def update_auth(self, account, permission, parent, controller):
        run(self.teclos_dir + ' --url' + self.host_address + ' push action eosio updateauth' + jsonArg({
            'account': account,
            'permission': permission,
            'parent': parent,
            'auth': {
                'threshold': 1, 'keys': [], 'waits': [],
                'accounts': [{
                    'weight': 1,
                    'permission': {'actor': controller, 'permission': 'active'}
                }]
            }
        }) + '-p ' + account + '@' + permission)

    def resign(self, account, controller):
        self.update_auth(account, 'owner', '', controller)
        self.update_auth(account, 'active', 'owner', controller)
        sleep(1)
        run(self.teclos_dir + ' get account ' + account)

    def resign_all(self):
        self.resign('eosio', 'eosio.prods')
        for a in self.systemAccounts:
            self.resign(a, 'eosio')

    def issue_token(self, total_amount, issue_amount):
        self.push_action('eosio.token', 'create',
                         "'[ \"eosio\", \"%s\", 0, 0, 0]' -p eosio.token" % Asset(total_amount))
        self.push_action('eosio.token', 'issue', "'[ \"eosio\", \"%s\", \"memo\" ]' -p eosio" % Asset(issue_amount))

    def reg_producers(self, accounts):
        for a in accounts:
            self.reg_producer(a)

    def reg_producer(self, a):
        run(self.teclos_dir + " --url %s system regproducer %s %s %s" % (
        self.host_address, a.name, a.keypair.public, "http://" + a.name + ".com/" + a.keypair.public))

    @staticmethod
    def transfer(host_address, sender, receipient, amount, memo=""):
        cmd = 'teclos --url %s transfer %s %s \"%s\" \"%s\"'
        run_retry(cmd % (host_address, sender, receipient, amount, memo))
