from feedscanner import FeedScanner
from http import client
import json

class RotationValidator:

    def __init__(self, connect_string, logpath):
        self.connect_string = connect_string
        self.scanner = FeedScanner(logpath)
        self.block_count = 0
        self.producer_schedule_index = 0
        self.scanner.subscribe('Produced block', self.on_block_produced)
        self.producer_schedule = []
        self.rotations = {}

    def on_block_produced(self, line):
        print(line)
        if len(self.producer_schedule) == 0:
            self.producer_schedule = self.get_producer_schedule()
        if self.block_count >= 12:
            ++self.producer_schedule_index
            self.block_count = 0
            print(self.producer_schedule_index)
        if self.producer_schedule[self.producer_schedule_index] in line:
            ++self.block_count
            print(self.block_count)
        else:
            print(self.producer_schedule[self.producer_schedule_index])

    def start(self):
        for _ in self.scanner.scan():
            print('')

    def get_rotations_object(self):
        conn = client.HTTPConnection(self.connect_string, 8888)
        body = {'scope': 'eosio', 'code': 'eosio', 'table': 'rotations', 'json': True}
        conn.request('POST', '/v1/chain/get_table_rows', json.dumps(body))
        response = conn.getresponse()
        return json.loads(response.read().decode('utf-8'))

    def get_producer_schedule(self):
        conn = client.HTTPConnection(self.connect_string, 8888)
        body = {'json': True}
        conn.request('POST', '/v1/chain/get_producers', json.dumps(body))
        response = conn.getresponse()
        producers = json.loads(response.read().decode('utf-8'))
        schedule = []
        for p in producers['rows']:
            schedule.append(p['owner'])
        schedule = schedule[:21]
        schedule.sort()
        return schedule
