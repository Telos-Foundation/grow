import csv
import sys
import time
import click
from bootstrapper import BootStrapper
from asset import Asset
from chain_api import ChainAPI

@click.group()
def cli():
    """Transcation Loop send TLOS around a test network using a snapshot of accounts"""

@cli.command()
@click.argument('csv-path', type=click.Path(exists=True))
def circular(csv_path):
    """Transfer TLOS around a csv snapshot!!!!"""
    api = ChainAPI('http://64.38.144.179:8888')
    prev = None
    while True:
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if prev is not None:
                    amt = api.get_currency_balance(row['account_name'])
                    BootStrapper.transfer('http://64.38.144.179:8888', row['account_name'], prev['account_name'], Asset(amt.amount / 4), 'From: %s To: %s' % (row['account_name'], prev['account_name']))
                prev = row
                #TODO: Do math on timestamp to determine next transfer

@cli.command()
def test():
    api = ChainAPI('http://64.38.144.179:8888')
    print(api.get_currency_balance('acctnamex1ww'))

@cli.command()
def loop():
    while True:
        print('doing things')
        time.sleep(1)

if __name__ == '__main__':
    cli()
