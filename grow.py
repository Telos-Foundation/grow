#!/usr/bin/env python3
from utility import *
from wallet import Wallet
from node_factory import NodeFactory
from account import AccountFactory
from bootstrapper import BootStrapper
from asset import Asset
import click
import json


class Grow:

    def __init__(self):
        self.parent_dir = os.path.abspath(join(os.path.realpath(__file__), os.pardir))
        self.jsonConfig = json.loads(file_get_contents(join(self.parent_dir, "config/state.json")))

        self.start_cwd = os.getcwd()
        self.contracts_dir = "build/contracts"
        self.wallet_dir = join(self.parent_dir, 'wallet')
        self.host_address = self.jsonConfig['host_address'] if 'host_address' in self.jsonConfig and self.jsonConfig[
            'host_address'] == "" else "http://localhost:8888"

        self.git_tag = ''
        self.telos_dir = os.path.abspath('telos')
        if 'src-dir' in self.jsonConfig and self.jsonConfig['src-dir'] != '':
            self.telos_dir = os.path.abspath(self.jsonConfig['src-dir'])
        self.keosd_dir = join(self.telos_dir, "build/programs/keosd/keosd")
        self.teclos_dir = join(self.telos_dir, "build/programs/teclos/teclos")
        self.nodeos_dir = join(self.telos_dir, "build/programs/nodeos/nodeos")

        self.wallet = Wallet(self.wallet_dir, self.teclos_dir, self.telos_dir, self.keosd_dir, 999999999)
        self.node_factory = NodeFactory(self.start_cwd, self.parent_dir, self.nodeos_dir, self.wallet)
        self.initializer = Initializer(self.telos_dir, self.start_cwd)
        self.account_factory = AccountFactory(self.wallet, self.teclos_dir)
        self.boot_strapper = BootStrapper(self.telos_dir, self.teclos_dir, self.host_address, self.account_factory)

    def set_host_address(self, address):
        self.host_address = address

    def save(self):
        self.node_factory.save()
        self.jsonConfig['host_address'] = self.host_address
        create_file(join(self.parent_dir, 'config/state.json'), json.dumps(self.jsonConfig, sort_keys=True, indent=4))


class Initializer:

    def __init__(self, telos, cwd):
        self.git_tag = 'developer'
        self.telos_dir = telos
        self.telos_repo_url = "https://github.com/Telos-Foundation/telos.git"
        self.start_cwd = cwd

    def set_tag(self, tag):
        self.git_tag = tag

    def reset_cwd(self):
        os.chdir(self.start_cwd)

    def pull(self):
        try:
            if os.path.exists(self.telos_dir):
                print("Path exists.")
                return
            dir = os.path.abspath(join(self.telos_dir, '..'))
            os.chdir(dir)
            run(['git clone %s --recursive' % self.telos_repo_url])
            os.chdir(self.telos_dir)
            if self.git_tag != "":
                run(['git', 'checkout', '-f', self.git_tag], False)
            run('git submodule update --init --recursive')
            self.reset_cwd()
            self.build_source()
        except OSError as e:
            print(e)

    def build_source(self):
        try:
            os.chdir(self.telos_dir)
            run(['./eosio_build.sh -s %s' % ('TLOS')])
            os.chdir(join(self.telos_dir, "build"))
            run('sudo make install')
            self.reset_cwd()
        except IOError as e:
            print(e)

    def update(self):
        try:
            os.chdir(join(self.telos_dir, 'telos'))
            run('git stash')
            run('git pull origin master')
            run('git checkout %s' % (self.git_tag))
            run('git submodule update --init --recursive')
            self.reset_cwd()
            self.build_eos()
        except IOError as e:
            print(e)


grow = Grow()


@click.group()
def cli():
    """Grow is a telos tool which allows you to start full nodes or producers nodes, and meshes. It also allows convenient access to teclos functions."""


@cli.group()
@click.option('--tag', default='developer')
def init(tag):
    """Initialize Grow with telos source, or update an existing source"""
    grow.initializer.set_tag(tag)


@init.command()
def pull():
    grow.initializer.pull()


@init.command()
def update():
    grow.initializer.update()


@cli.group()
def spin():
    """Spin up producer nodes, full nodes, and meshes using nodeos"""


@spin.command()
@click.argument('http-port')
@click.argument('p2p-port')
@click.argument('p2p-address')
@click.option('--path', default=os.getcwd())
@click.option('--fund-account', default=False)
def full(http_port, p2p_port, p2p_address, path, fund_account):
    """Start a genesis node"""
    grow.wallet.unlock()
    grow.node_factory.start_full(path, p2p_address, http_port, p2p_port)
    grow.boot_strapper.boot_strap_node('http://localhost:%s' % http_port)
    if fund_account:
        grow.boot_strapper.create_fund_account()
    grow.save()


@spin.command()
@click.argument('http-address')
@click.argument('p2p-port')
@click.argument('p2p-address')
@click.option('--path', default=os.getcwd())
def single(path):
    """Start a single producer node"""
    print('Not implemented currently')


@spin.command()
@click.argument('num-nodes', type=int, default=21)
@click.argument('path', default=os.getcwd())
@click.option('--min-stake', type=float, default=0.01)
@click.option('--max-stake', type=float, default=0.02)
def mesh(path, num_nodes, min_stake, max_stake):
    """Start a private mesh of nodes"""
    grow.wallet.unlock()
    grow.node_factory.start_full(path, '0.0.0.0', str(8888), str(9876))
    grow.boot_strapper.boot_strap_node('http://localhost:%s' % str(8888))
    accounts = grow.account_factory.create_random_accounts(num_nodes, BootStrapper.token_issue * min_stake,
                                                           BootStrapper.token_issue * max_stake)
    grow.node_factory.start_producers_by_account(accounts, num_nodes)
    grow.save()


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


@spin.command('show-output')
@click.argument('name')
def show_output(name):
    """Show node ouput of named node"""
    try:
        n = grow.node_factory.get_node_from_state(name)
        n.show_output()
    except ValueError as e:
        print(e)


@spin.command('show-nodes')
def show_nodes():
    """Display running nodes"""
    print(grow.node_factory.get_nodes().replace('\\', ''))


@spin.command('reset')
def reset():
    """Stops and then deletes all nodes"""
    i = input('This will stop all nodes and delete their folders, and remove state. Are you sure you want this? (Y/n)\n')
    print(i)
    if i.lower() == 'yes' or i.lower() == 'y':
        grow.node_factory.delete_all_nodes()

@spin.command()
def test_port_scan():
    """Test that socket is finding open ports"""
    print(grow.node_factory.get_open_port())
    grow.save()


@cli.group()
@click.option('--url', default='http://localhost:8888')
def accounts(url):
    """Create accounts on a test net"""
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
@click.option('--cpu', type=int, default=100)
@click.option('--net', type=int, default=100)
@click.option('--ram', type=int, default=100)
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
    print('Not currently implemented')
    #grow.account_factory.create_accounts_from_csv(path)


@cli.group()
def wallet():
    """Lock, unlock, and create keys"""


@wallet.command()
def unlock():
    """Unlock telos wallet"""
    grow.wallet.unlock()


@wallet.command()
def lock():
    """Lock telos wallet"""
    grow.wallet.lock()


@wallet.command('show-keys')
def private_keys():
    """Show public and private keys"""
    print(json.dumps(grow.wallet.get_keys(), indent=4, sort_keys=True).replace('\\', ''))


@wallet.command('key-gen')
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


if __name__ == '__main__':
    cli()

#     if args.private_test:
#         producer_accounts = create_random_accounts(21, (args.token_issue * 0.01), (args.token_issue * 0.02), "prodname")
#         normal_accounts = create_random_accounts(30, (args.token_issue * 0.01), (args.token_issue * 0.02))
#         jsonConfig['node_index'] = 30 - 1
#         reg_producers(producer_accounts)
#         start_all_nodes(producer_accounts)
#         vote_producers(producer_accounts, producer_accounts)
#         vote_producers(normal_accounts, producer_accounts)
#         time.sleep(60)
#         resign_all()
