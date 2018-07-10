#!/usr/bin/env python
import argparse
import subprocess
import json
import time
import sys
import os
import re
import string
import csv
from random import randint
from shutil import copyfile
from shutil import rmtree
from tlos_utility import *
from tlos_wallet import tlos_wallet

class Asset:
    symbol = ''
    amount = 0.0000

    def __init__(self, amount, symbol = 'TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % (format(self.amount, '.4f'), self.symbol)


#region system utilities

def reset_cwd():
    os.chdir(start_cwd)

#endregion

def get_repository():
    if os.path.exists(eos_dir):
        print "Path exists."
        return
    run(['git clone %s --recursive' % telos_repo_url, '--directory ', eos_dir])
    print 'changing to eos directory: ' + eos_dir
    os.chdir(eos_dir)
    if args.tag_name != "":
        run(['git', 'checkout', '-f', args.tag_name], False)
    run('git submodule update --init --recursive')
    reset_cwd()
    build_eos()

def build_eos():
    os.chdir(eos_dir)
    run(['./eosio_build.sh -s %s' % (args.symbol)])
    os.chdir(os.path.join(eos_dir, "build"))
    print "Compiling executables and binaries... You may need to enter your password."
    run('sudo make install')
    reset_cwd()

def update_repository():
    print "update_repository()"
    os.chdir(eos_dir)
    run('git stash')
    run('git pull origin master')
    run('git checkout %s' % (args.tag_name))
    run('git submodule update --init --recursive')
    reset_cwd()
    build_eos()

#region accounts
def create_account_cmd(account_name, public_key):
    run( teclos_dir + ' create account eosio %s %s' % (account_name, public_key))

def create_account_obj(account_name):
    a = {}
    a['name'] = account_name
    a['keys'] = wallet.create_key()
    wallet.import_key(a['keys']['private'])
    return a

def create_accounts_from_csv(path_to_csv):
    try:
        with open(path_to_csv, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                amt = float(row['token_amt'])
                liquid = 0.1000 if amt < 3.0000 else 10.0000 if amt > 11.000 else 2.0000 
                remainder = amt - liquid
                cpu = remainder / 2
                net = remainder - cpu
                if cpu + net + liquid == amt:
                    print 'name: %s, amt: %s, liquid: %s, cpu: %s, net: %s, total: %s' % (row['name'], format(amt, '.4f'), liquid, cpu, net, format((cpu + net + liquid), '.4f'))
                else:
                    print (cpu + net + liquid) + ' != ' 
    except Exception as e:
        print "unable to parse csv and create accounts"
        print e.message

def create_staked_account(a, net, cpu, ram):
    cmd = teclos_dir + ' system newaccount eosio --transfer %s %s --stake-net \"%s\" --stake-cpu \"%s\" --buy-ram \"%s\"'
    run_retry(cmd % (a['name'], a['keys']['public'], net, cpu, ram))

def create_system_accounts(account_names):
    accounts = []
    wallet.unlock()
    for account in account_names:
        a = create_account_obj(account['name'])
        create_account_cmd(a['name'], a['keys']['public'])
        accounts.append(a)
    return accounts

def create_random_accounts(num_accounts, min, max, base = "acctname"):
    accounts = []
    for _ in range(num_accounts):
        a = create_account_obj(base + id_generator())
        create_staked_account(a, Asset(randint(min, max)), Asset(randint(min, max)), Asset(randint(min, max)))
        accounts.append(a)
    return accounts
#endregion

def set_system_contracts(contract_names):
    for contract in contract_names:
        name = contract['name']
        path = os.path.join(os.path.join(os.path.abspath(eos_dir), os.path.join(contracts, name)))
        set_contract(contract['owner'], path)

def set_contract(account_name, path, p = ""):
    cmd = teclos_dir + ' --url %s set contract %s %s'
    if p != "":
        cmd += ' -p %s' % p
    run_retry(cmd % (host_address, account_name, path))

def push_action(target, action_name, json):
    run_retry(teclos_dir + ' --url %s push action %s %s %s' % (host_address, target, action_name, json))
    
def vote_producers(a_accounts, b_accounts):
    print "vote_producers()"
    for a in a_accounts:
        cmd = teclos_dir + ' system voteproducer prods ' + a['name'] + ''
        i = 0
        for t in b_accounts:
            if a['name'] not in t['name'] and i < randint(10, 30):
                cmd += t['name'] + " "
                i = i + 1
        run_retry(cmd)

def update_auth(account, permission, parent, controller):
    run(teclos_dir + ' push action eosio updateauth' + jsonArg({
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

def resign(account, controller):
    update_auth(account, 'owner', '', controller)
    update_auth(account, 'active', 'owner', controller)
    time.sleep(1)
    run(teclos_dir + ' get account ' + account)

def resign_all():
    resign('eosio', 'eosio.prods')
    for a in systemAccounts:
        resign(a, 'eosio')

def issue_token(total_amount, issue_amount):
    print "issue_token()"
    push_action('eosio.token', 'create', "'[ \"eosio\", \"%s\", 0, 0, 0]' -p eosio.token" % Asset(total_amount))
    push_action('eosio.token', 'issue', "'[ \"eosio\", \"%s\", \"memo\" ]' -p eosio" % Asset(issue_amount))

def reg_producers(accounts):
    print "reg_producers()"
    for a in accounts:
        reg_producer(a)

def reg_producer(a):
    print("reg_producer()")
    run(teclos_dir + " --url %s system regproducer %s %s %s" % (host_address, a['name'], a['keys']['public'], "http://" + a['name'] + ".com/" + a['keys']['public']))

def transfer(sender, receipient, amount, memo = ""):
    cmd = teclos_dir + ' transfer %s %s \"%s %s\" \"%s\"'
    run_retry(cmd % (sender, receipient, amount, args.symbol, memo))

#region node management
def start_full():
    print "start_full()"
    try:
        dir = os.path.join(start_cwd, 'en-full-node')
        os.makedirs(dir)
        copyfile(os.path.join(parent_dir, 'config/full_config.ini'), os.path.join(dir, 'config.ini'))
        copyfile(os.path.join(parent_dir, 'config/genesis.json'), os.path.join(dir, "genesis.json"))
        os.chdir(dir)
        cmd = build_full_node_cmd(dir)
        cmd += ' --delete-all-blocks'
        cmd += " --genesis-json %s" % os.path.join(dir, "genesis.json")
        start_background_proc(cmd, log_file(os.path.join(start_cwd, os.path.join(dir, 'stderr.txt'))))
        reset_cwd()
    except OSError as e:
        print ('Error occurred while attempting to get configuration file! Message: %s' % e.message)

def restart_full():
    print "restart_full()"
    dir = os.path.join(start_cwd, 'en-full-node')
    os.chdir(dir)
    cmd = build_full_node_cmd(dir)
    start_background_proc(cmd, log_file(os.path.join(start_cwd, os.path.join(dir, 'stderr.txt'))))

def start_node(node_index, account):
    dir =  os.path.join(start_cwd, 'en-' + str(node_index) + '_' + account['name'])
    os.makedirs(dir)
    copyfile(os.path.join(parent_dir, "config/test_config.ini"), os.path.join(dir, "config.ini"))
    copyfile(os.path.join(parent_dir, "config/genesis.json"), os.path.join(dir, "genesis.json"))
    os.chdir(dir)
    start_background_proc(build_private_node_cmd(node_index, account, dir), log_file(os.path.join(start_cwd, os.path.join(dir, 'stderr.txt'))))
    reset_cwd()

def build_full_node_cmd(path):
    cmd = nodeos_dir + ' --blocks-dir %s' % (os.path.join(path, "blocks"))
    cmd += " --config-dir %s" % (path)
    cmd += " --hard-replay-blockchain"
    return cmd

def build_private_node_cmd(node_index, account, path):
    otherOpts = ' --p2p-peer-address localhost:9876'.join(list(map(lambda i: '    --p2p-peer-address localhost:' + str(9000 + i), range(node_index))))
    cmd = nodeos_dir + " --config-dir " + path
    cmd += " --genesis-json " + os.path.join(path, "genesis.json")
    cmd += " --blocks-dir " + os.path.join(path, "blocks")
    cmd += " --http-server-address 127.0.0.1:" + str(8000 + node_index)
    cmd += " --p2p-listen-endpoint 127.0.0.1:" + str(9000 + node_index)
    cmd += " --producer-name " + account['name']
    cmd += " --signature-provider = " + account['keys']['public'] + "=KEY:" + account['keys']['private']
    cmd += " --delete-all-blocks"
    cmd += " --hard-replay-blockchain"
    cmd += otherOpts
    return cmd

def start_all_nodes(accounts):
    i = 0
    for a in accounts:
        start_node(i, a)
        i = i + 1

def stop_all_nodes():
    run_continue('pkill -f nodeos')

def delete_all_nodes():
    stop_all_nodes()
    for dir in os.listdir(start_cwd):
        if folder_scheme in dir:
            rmtree(dir)

def reset():
    delete_all_nodes()
    run_continue('pkill -f keosd')
    rmtree(os.path.join(os.path.expanduser('~'), 'telos-wallet'))
    rmtree(os.path.join(parent_dir, 'wallet'))
#endregion

parser = argparse.ArgumentParser(description='This is the EOSIO boot strap for full-node deployment')

parser.add_argument('--snapshot', help='Create accounts from snapshot')
parser.add_argument('--create-account', help='Creates and account and returns a json representation with: name, public key, private key')
parser.add_argument('--token-supply', help="Max number of TELOS tokens", dest="token_supply", default=10000000000)
parser.add_argument('--token-issue', help="Number TELOS to issue", dest="token_issue", default=190473249)
parser.add_argument('--private-Key', help="EOSIO Private Key", dest="private_key", default="5JfkiC1um2SEqvJ3gcvxikoDy5R9HALsA553x2iYwvzt4pNL5bH")
parser.add_argument('--unlock-wallet', action="store_true", help="Unlock you wallet")
parser.add_argument('--lock-wallet', action="store_true", help="Lock you wallet")
parser.add_argument('--token-symbol', help="The eosio.system symbol", default='TLOS', dest='symbol')
parser.add_argument('--tag-name', help="git repository tag name to pull", default="developer")
parser.add_argument('--rebuild-eos', help="Rebuild EOSIO software", action='store_true')
parser.add_argument('--pull-repo', action="store_true", help="Pull eos from gitub")
parser.add_argument('--update-repo', action="store_true", help="Update repository ")
parser.add_argument('--eos-dir', help='Absolute path to eos directory', default="telos")
parser.add_argument('--boot-strap', action="store_true", help='Boot strap a full node')
parser.add_argument('--fund-account', action="store_true", help='Create a fund account when boot-straping a full node')
parser.add_argument('--start-single', help='Start a single node for a testnet')
parser.add_argument('--start-full', action='store_true', help='Start a genesis node to start a testnet')
parser.add_argument('--private-test', action='store_true', help="Create a private Testnet with several nodes running on your computer")
parser.add_argument('--reset', action="store_true", help="Deletes all running nodes that use the en- folder scheme, and deletes local wallet")

args = parser.parse_args()

this_file_dir = os.path.realpath(__file__)
parent_dir = os.path.abspath(os.path.join(this_file_dir, os.pardir))
start_cwd = os.getcwd()

telos_repo_url = "https://github.com/Telos-Foundation/telos.git"

folder_scheme = "en-"
jsonConfig = json.loads(file_get_contents(os.path.join(parent_dir, "config/config.json")))
host_address = jsonConfig['node_address'] if 'node_address' in jsonConfig and jsonConfig['node_address'] == "" else "http://localhost:8888"
wallet_dir = os.path.join(parent_dir, 'wallet')
eos_dir = os.path.abspath(args.eos_dir) if 'eos-source-dir' not in jsonConfig or jsonConfig['eos-source-dir'] == "" else os.path.abspath(jsonConfig['eos-source-dir'])
contracts = "build/contracts"
keosd_dir = os.path.join(eos_dir, "build/programs/keosd/keosd")
teclos_dir = os.path.join(eos_dir, "build/programs/teclos/teclos")
nodeos_dir = os.path.join(eos_dir, "build/programs/nodeos/nodeos")
systemAccounts = jsonConfig['system-accounts']
systemContracts = jsonConfig['system-contracts']

if args.reset:
    reset()
    sys.exit(0)

wallet = tlos_wallet(wallet_dir, teclos_dir, eos_dir, keosd_dir, 999999999)

if args.pull_repo:
    get_repository()

if args.rebuild_eos:
    build_eos()

if not os.path.isdir(eos_dir):
    print "EOS software does not appear to be installed"
    sys.exit(1)

if args.unlock_wallet:
    wallet.unlock()

if args.lock_wallet:
    wallet.lock()

if 'create_account' in args and args.create_account != "" and args.create_account != None:
    wallet.unlock()
    print json.dumps(create_account_obj(args.create_account))

if args.start_full:
    wallet.unlock()
    if not wallet.contains_key(args.private_key):
        wallet.import_key(args.private_key)
    if not os.path.isdir(os.path.join(start_cwd, "en-full-node")):
        start_full()
        time.sleep(10)
        args.boot_strap = True
    else:
        restart_full()

if 'start_single' in args and args.start_single != "" and args.start_single != None:
    print "start_single()"
    print jsonConfig['node_index']

if args.boot_strap:
    wallet.unlock()
    if not wallet.contains_key(args.private_key):
        wallet.import_key(args.private_key)
    system_accounts = create_system_accounts(systemAccounts)
    set_system_contracts(systemContracts)
    issue_token(args.token_supply, args.token_issue)
    run(teclos_dir + ' set contract eosio telos/build/contracts/eosio.system -p eosio')
    run(teclos_dir + ' push action eosio setpriv \'[\"eosio.msig\", 1]\' -p eosio@active')
    if args.fund_account:
        print "Creating fund account"
        fund_account = create_account_obj('telosfundacc')
        create_staked_account(fund_account, Asset(1000.0000), Asset(1000.0000), Asset(1000.0000))
        transfer('eosio', fund_account['name'], str(args.token_issue * 0.15), "Sending 15 percent stake and enough money to create new accounts")

if 'snapshot' in args and args.snapshot != "" and args.snapshot != None:
    if os.path.isfile(args.snapshot):
        create_accounts_from_csv(args.snapshot)

if args.private_test:
    producer_accounts = create_random_accounts(21, (args.token_issue * 0.01), (args.token_issue * 0.02), "prodname")
    normal_accounts = create_random_accounts(30, (args.token_issue * 0.01), (args.token_issue * 0.02))
    jsonConfig['node_index'] = 30 - 1
    reg_producers(producer_accounts)
    start_all_nodes(producer_accounts)
    vote_producers(producer_accounts, producer_accounts)
    vote_producers(normal_accounts, producer_accounts)
    time.sleep(60)
    resign_all()

create_file(os.path.join(parent_dir, 'config/config.json'), json.dumps(jsonConfig))