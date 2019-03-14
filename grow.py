#!/usr/bin/env python3
from utility import *
from wallet import Wallet
from node_factory import NodeFactory
from account import AccountFactory
from account import Account
from bootstrapper import BootStrapper
from rotation_validator import RotationValidator
from feedscanner import FeedScanner
from sys import exit
import click
import json
import re


class Grow:

    def __init__(self):
        self.parent_dir = os.path.abspath(join(os.path.realpath(__file__), os.pardir))
        self.jsonConfig = json.loads(file_get_contents(join(self.parent_dir, "config/state.json")))

        self.start_cwd = os.getcwd()
        self.wallet_dir = join(self.parent_dir, 'wallet')
        self.host_address = self.jsonConfig['host_address'] if 'host_address' in self.jsonConfig and self.jsonConfig[
            'host_address'] == "" else "http://127.0.0.1:8888"

        self.contracts_dir = ''
        if 'contract-path' in self.jsonConfig and self.jsonConfig['contract-path'] != '':
            self.contracts_dir = self.jsonConfig['contract-path']

        self.keosd = "keosd"
        self.cleos = "cleos"
        self.nodeos = "nodeos"

    def setup(self):

        if not self.isCdt():
            print('Grow requires that eosio.cdt be install')
            print('Please install the cdt and try again')
            exit(2)

        if not self.isNodeos():
            print('Grow requires nodeos to be installed and in the path variable')
            exit(2)

        if not self.isCleos():
            print('Grow requires cleos to be installed and in the path variable')
            exit(2)

        if not self.isKeosd():
            print('Grow requires keosd to be installed and in the path variable')
            exit(2)

        if not os.path.exists(self.contracts_dir):
            print('eosio.contracts source either doesn\'t exist, or isn\'t initialized')
            exit(2)

        self.wallet = Wallet(self.wallet_dir, self.cleos, self.keosd, 10000)
        self.node_factory = NodeFactory(self.start_cwd, self.parent_dir, self.nodeos, self.wallet)
        self.account_factory = AccountFactory(self.wallet, self.cleos)
        self.boot_strapper = BootStrapper(self.contracts_dir, self.cleos, self.host_address, self.account_factory)

    def isCdt(self):
        output = get_output('eosio-cpp --version')
        return re.match('eosio-cpp version (!?[0-9].[0-9](.[0-9])?)', output)

    def isNodeos(self):
        output = get_output('nodeos --version')
        return re.match('v(!?[0-9].[0-9](.[0-9])?)', output)

    def isKeosd(self):
        output = get_output('keosd --version')
        return re.match('v(!?[0-9].[0-9](.[0-9])?)', output)

    def isCleos(self):
        output = get_output('cleos version client')
        return re.match('Build version: ', output)


    def get_contracts_path(self):
        return self.contracts_dir

    def set_host_address(self, address):
        self.host_address = address

    def save(self):
        if hasattr(self, 'node_factory'):
            self.node_factory.save()
        self.jsonConfig['host_address'] = self.host_address
        create_file(join(self.parent_dir, 'config/state.json'), json.dumps(self.jsonConfig, sort_keys=True, indent=4))

    @staticmethod
    def get_chain_id():
        j = json.loads(get_output('teclos get info'))
        return j['chain-id']

grow = Grow()


# TODO: Start a background thread that sends a number of transactions per second

# TODO: Continuously test transaction receipts, log irregular activity

@click.group()
def cli():
    """Grow is a telos tool which allows you to start full nodes or producers nodes, and meshes. It also allows convenient access to teclos functions."""


@cli.group()
@click.option('--tag')
def init(tag):
    """Initialize Grow with telos source, or update an existing source"""

@init.command('setsource')
@click.argument('contract-src-path', type=click.Path(exists=True))
def set_src(telos_src_path, contract_src_path):
    """Set grows telos source to an existing directory"""

    grow.set_source_path(telos_src_path, contract_src_path)
    print('eosio.contracts source was set to path %s' % (contract_src_path))


@init.command('getsource')
def print_source():
    """Print the current Telos source path"""
    print(grow.get_contracts_path())


@cli.group()
def spin():
    """Spin up producer nodes, full nodes, and meshes using nodeos"""
    grow.setup()


@spin.command()
@click.argument('http-port')
@click.argument('p2p-port')
@click.argument('p2p-address')
@click.option('--path', default=os.getcwd())
@click.option('--fund-account', default=False)
@click.option('--boot-strap', default=True)
@click.option('--plugin', multiple=True)
def full(http_port, p2p_port, p2p_address, path, fund_account, boot_strap, plugin):
    """Start a genesis node"""
    try:
        grow.wallet.unlock()
        grow.node_factory.start_full(path, p2p_address, http_port, p2p_port, list(plugin))
        if boot_strap is True:
            grow.boot_strapper.boot_strap_node('http://127.0.0.1:%s' % http_port)
        if fund_account is True and boot_strap is True:
            grow.boot_strapper.create_fund_account()
    except KeyError as e:
        print(e)
    finally:
        grow.save()


@spin.command()
@click.argument('producer-name')
@click.argument('p2p-address')
@click.argument('genesis-json-path')
@click.argument('genesis-node-address')
@click.option('--p2p-port', default='9876')
@click.option('--http-port', default='8888')
@click.option('--path', default=os.getcwd())
def single(producer_name, p2p_address, genesis_json_path, genesis_node_address, p2p_port, http_port, path):
    """Start a single producer node"""
    grow.node_factory.start_single(producer_name, path, p2p_address, http_port, p2p_port, genesis_node_address,
                                   genesis_json_path)


@spin.command()
@click.argument('num-nodes', type=int, default=21)
@click.argument('path', default=os.getcwd())
@click.option('--genesis-http-port', default=8888)
@click.option('--genesis-p2p-port', default=9876)
@click.option('--dist-percentage', default=60)
@click.option('--no-vote', type=bool, default=False)
@click.option('--vote-self', type=bool, default=False)
@click.option('--num-self-voters', type=int, default=15)
@click.option('--plugin', multiple=True)
def mesh(path, num_nodes, genesis_http_port, genesis_p2p_port, dist_percentage, no_vote, vote_self, num_self_voters,
         plugin):
    """Start a private mesh of nodes"""
    # TODO: reserve TLOS tokens for account creation, use 10%
    try:
        max_stake = (dist_percentage / num_nodes) / 100 / 3
        min_stake = max_stake / 2
        total = (max_stake * 3 * 100 * num_nodes)
        assert (total <= dist_percentage)

        grow.wallet.unlock()
        grow.node_factory.start_full(path, '0.0.0.0', str(genesis_http_port), str(genesis_p2p_port), list(plugin))
        grow.boot_strapper.boot_strap_node('http://127.0.0.1:%s' % str(genesis_http_port))
        producers = grow.account_factory.create_random_accounts(num_nodes, BootStrapper.token_issue * min_stake,
                                                                BootStrapper.token_issue * max_stake, 'prodname')
        grow.boot_strapper.reg_producers(producers)
        grow.node_factory.start_producers_by_account(producers, path)
        if vote_self:
            grow.boot_strapper.self_vote_producers(producers, num_self_voters)
        elif not no_vote:
            grow.boot_strapper.vote_producers(producers, producers)

    except KeyError as e:
        print(e)
    finally:
        grow.save()


@spin.command()
@click.argument('path', default=os.getcwd())
def mesh_add(path):
    grow.wallet.unlock()
    prod = grow.account_factory.create_random_accounts(1, 2000.0000, 2000.0000, 'prodname')[0]
    grow.node_factory.start_producers_by_account([prod], path)
    grow.boot_strapper.reg_producers([prod])
    tmp = grow.node_factory.get_producer_names()
    prods = []
    for prod in tmp:
        prods.append(Account(prod, {}))
    grow.boot_strapper.self_vote_producers(prods)
    grow.node_factory.save()


@spin.command()
@click.argument('name')
def restart(name):
    """Restart the node with the given name"""
    try:
        print('Restarting node %s' % name)
        n = grow.node_factory.get_node_from_state(name)
        n.restart()
        grow.node_factory.save()
        time.sleep(0.2)
        grow.node_factory.get_status(name)
    except ValueError as e:
        print(e)


@spin.command()
@click.argument('name')
def stop(name):
    """Stop the node with the given name"""
    try:
        print('Stopping node %s' % name)
        n = grow.node_factory.get_node_from_state(name)
        n.stop()
        grow.node_factory.save()
        time.sleep(0.2)
        grow.node_factory.get_status(name)
    except ValueError as e:
        print(e)


@spin.command()
@click.argument('name')
def status(name):
    """Show the running status of named node"""
    try:
        grow.node_factory.get_status(name)
    except ValueError as e:
        print(e)


@spin.command('output')
@click.argument('name')
def show_output(name):
    """Show node ouput of named node"""
    try:
        n = grow.node_factory.get_node_from_state(name)
        n.show_output()
    except ValueError as e:
        print(e)


@spin.command('nodes')
def show_nodes():
    """Display running nodes"""
    print(grow.node_factory.get_nodes().replace('\\', ''))


@spin.command('reset')
def reset():
    """Stops and then deletes all nodes"""
    i = input(
        'This will stop all nodes and delete their folders, and remove state. Are you sure you want this? (Y/n)\n')

    if i.lower() == 'yes' or i.lower() == 'y':
        grow.node_factory.delete_all_nodes()


# @spin.command()
# def test_port_scan():
#     """Test that socket is finding open ports"""
#     print(grow.node_factory.get_open_port())
#     grow.save()


@cli.group()
@click.option('--url', default='http://127.0.0.1:8888')
def accounts(url):
    """Create accounts on a test net"""
    grow.setup()
    grow.account_factory.set_host_address(url)
    grow.set_host_address(url)
    grow.save()


@accounts.command()
@click.option('--count', default=1)
def gen(count):
    """Generate Random Accounts on a net"""
    grow.account_factory.create_random_accounts(count, 100, 1000)


@accounts.command()
@click.argument('name')
@click.option('--json-only/--json', default=False)
@click.option('--cpu', type=float, default=100)
@click.option('--net', type=float, default=100)
@click.option('--ram', type=float, default=100)
@click.option('--creator', default='eosio')
def create(name, json_only, cpu, net, ram, creator):
    """Generate a json account object, and import keys"""
    if json_only:
        print(grow.account_factory.get_acc_obj(name))
    else:
        a = grow.account_factory.get_acc_obj(name, True)
        grow.account_factory.post_sys_create(a, net, cpu, ram, creator)


@accounts.command()
@click.argument('path', type=click.Path(exists=True))
def snapshot(path):
    """Create all the accounts from snapshot file"""
    # print('Not currently implemented')
    # grow.account_factory.create_accounts_from_csv(path)
    grow.account_factory.threaded_snapshot_injection(4, path)


@accounts.command('randshot')
@click.argument('path', type=click.Path())
@click.option('--num-accounts', type=int, default=100)
@click.option('--min-stake', type=int, default=10)
@click.option('--max-stake', type=int, default=100)
@click.option('--base-name', type=str, default='acctname')
def create_random_snapshot(path, num_accounts, min_stake, max_stake, base_name):
    """Create a snapshot of random accounts"""
    grow.account_factory.create_random_snapshot(num_accounts, min_stake, max_stake, path, base_name)


@cli.group()
def wallet():
    """Lock, unlock, and create keys"""
    grow.setup()


@wallet.command()
def unlock():
    """Unlock telos wallet"""
    grow.wallet.unlock()


@wallet.command()
def lock():
    """Lock telos wallet"""
    grow.wallet.lock()


@wallet.command('keys')
def private_keys():
    """Show public and private keys"""
    print(json.dumps(grow.wallet.get_keys(), indent=4, sort_keys=True).replace('\\', ''))


@wallet.command('keygen')
@click.option('--json-only/--json', default=False)
def gen(json_only):
    """Create a keypair"""
    if json_only:
        print(grow.wallet.create_key())
    else:
        print(grow.wallet.create_import())


@wallet.command('reset')
def reset_wallet():
    """Stops and then deletes all nodes"""
    i = input('This will destroy your wallet and terminate the keosd process. Are you sure you want that? (Y/n)')

    if i.lower() == 'yes' or i.lower() == 'y':
        grow.wallet.reset()


@cli.group()
def chain():
    """Short hand chain actions"""


@chain.command()
@click.argument('target')
@click.option('--transactions-only', type=bool, default=False)
@click.option('--block-key', type=str)
def getblocks(target, transactions_only, block_key):
    """get blocks by number or range"""
    if '-' in target:
        floor = int(target[0: target.index('-')].strip())
        ceil = int(target[target.index('-') + 1: len(target)].strip())
        if ceil > floor:
            result = {}
            for i in range(floor, ceil):
                o = json.loads(get_output('teclos get block %d' % i))
                if transactions_only and len(o['transactions']) > 0:
                    result[i] = o
                elif block_key in o and o[block_key] is not None:
                    result[i] = o
                elif not transactions_only and not block_key:
                    result[i] = o
            print(json.dumps(result, indent=4, sort_keys=True))
        else:
            print('ceil is less than floor')
    else:
        print(get_output('teclos get block %d' % target))


@chain.command()
@click.argument('path')
def validate_rotations(path):
    validator = RotationValidator('127.0.0.1', path)
    validator.start()


# TODO: Setup chain actions module
# TODO: get list of producers sorted by name

if __name__ == '__main__':
    cli()
