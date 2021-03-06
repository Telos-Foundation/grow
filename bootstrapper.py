import os
import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from utility import jsonArg
from utility import run
from utility import run_retry
from utility import join
from utility import file_get_contents
from utility import get_output
from random import randint
from time import sleep
from asset import Asset
from json import dumps as toJson
from json import loads as fromJson

import requests


class BootStrapper:
    token_supply = 10000000000
    token_issue = 190473249

    def __init__(self, parent_dir, contracts, teclos, host_address, account_factory):
        self.contracts_dir = join(os.path.abspath(contracts), 'build/contracts')
        self.teclos_dir = teclos
        self.host_address = host_address
        self.account_factory = account_factory
        accounts = fromJson(file_get_contents(parent_dir + '/config/accounts.json'))
        self.pre_accounts = accounts['pre-accounts']
        self.post_accounts = accounts['post-accounts']

    def set_host_address(self, address):
        self.host_address = address

    def boot_strap_node(self, address):
        self.set_host_address(address)
        self.account_factory.set_host_address(address)
        # TODO: Make sure full node has eosio root key in wallet
        self.account_factory.create_pre_accounts(self.pre_accounts)
        self.set_system_contracts(self.pre_accounts)
        self.issue_token(self.token_supply, self.token_issue)
        system_contract = join(self.contracts_dir, 'eosio.system')
        res = requests.post(self.host_address + '/v1/producer/schedule_protocol_feature_activations', data=toJson({'protocol_features_to_activate': ["0ec7e080177b2c02b278d5088611686b49d739925a92d9bfcacd7fc6b74053bd"]}))
        print(res)
        print(res.content)
        sleep(2)
        run(self.teclos_dir + ' --url %s set contract eosio %s -p eosio' % (self.host_address, system_contract))
        args = toJson([0, "4,TLOS"])
        run(self.teclos_dir + ' --url %s push action eosio init \'%s\' -p eosio' % (self.host_address, args))
        run(self.teclos_dir + ' --url %s push action eosio setpriv \'[\"eosio.msig\", 1]\' -p eosio@active' %
            self.host_address)

        self.account_factory.create_post_accounts(self.post_accounts, self.setup_post_account)

    def setup_post_account(self, post_account):
        if('contract' in post_account):
            self.set_contract(post_account.name, post_account.contract.path, post_account.name)
            # TODO: create trx and send it
            if('init' in post_account.contract):
                self.push_transaction(post_account.contract.init)
        if('actions' in post_account):
            self.push_transaction(post_account.actions)

    def push_transaction(self, actions):
        trx = {
            'max_net_usage_words': 0,
            'max_cpu_usage_ms': 0,
            'delay_sec': 0,
            'context_free_actions': [],
            'actions': actions,
            'transaction_extensions': [],
            'signatures': [],
            'context_free_data': []
        }
        trx = {**trx, **self.get_trx_header()}

        run("cleos push transaction '{}'".format(toJson(trx)))

    def get_trx_header(self, seconds_ahead=30):
        o = fromJson(get_output('cleos get info'))
        lib = o['last_irreversible_block_num']
        exp = parse(o['head_block_time']) + relativedelta(minutes=seconds_ahead)
        p = fromJson(get_output('cleos get block {}'.format(lib)))
        return {'expiration': exp.isoformat(), 'ref_block_num': lib, 'ref_block_prefix':  p['ref_block_prefix']}

    def create_fund_account(self):
        a = self.account_factory.get_acc_obj('telosfundacc')
        self.account_factory.post_sys_create(a, (self.token_issue * 0.15) / 2,
                                             (self.token_issue * 0.15) / 2, 1000.0000)
        BootStrapper.transfer(self.host_address, 'eosio', a.name, Asset(1000.0000),
                              "Sending 15 percent stake and enough money to create new accounts")

    def set_system_contracts(self, contract_names):
        try:
            for contract in contract_names:
                if 'contract' in contract:
                    name = contract['contract']
                    path = join(self.contracts_dir, name)
                    self.set_contract(contract['name'], path, contract['name'])
        except IOError as e:
            print(e)

    def set_contract(self, account_name, path, p=""):
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
        cmd = 'cleos --url %s transfer %s %s \"%s\" \"%s\"'
        run_retry(cmd % (host_address, sender, receipient, amount, memo))
