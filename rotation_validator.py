from feedscanner import FeedScanner
from http import client
import json
import re

class RotationValidator:

    def __init__(self, connect_string, logpath):
        self.connect_string = connect_string
        self.scanner = FeedScanner(logpath)
        self.block_count = 0
        self.producer_schedule_index = 0
        self.scanner.subscribe('Produced block', self.on_block_produced)
        self.scanner.subscribe('Received block', self.on_block_produced)
        self.last_to_producer = ""
        self.producer_schedule = []
        self.current_schedule_results = {}
        self.rotations = {}
        self.fast_forward = True

    def on_block_produced(self, line):
        print(line)
        signed_by = self.get_producer_from_line(line)
        if len(self.producer_schedule) == 0:
            self.producer_schedule = self.get_producer_schedule()
            if len(self.producer_schedule) == 0:
                return
        if self.producer_schedule_index > 20:
            self.producer_schedule_index = 0
        current = self.producer_schedule[self.producer_schedule_index]
        if self.fast_forward:
            print('Fast Forwarding')
            self.producer_schedule_index = self.producer_schedule.index(signed_by)
            print('New Index: ' + str(self.producer_schedule_index))
            self.fast_forward = False
        if signed_by != self.last_to_producer:
            print('current producer changed: from %s to %s' % (self.last_to_producer, current))
            self.current_schedule_results[current] = self.block_count
            self.producer_schedule_index = self.producer_schedule_index + 1
            self.block_count = 0
        if current in line:
            self.block_count = self.block_count + 1
            print(self.block_count)
        else:
            print('current: ' + self.producer_schedule[self.producer_schedule_index])
            print('last: ' + self.last_to_producer)
        self.last_to_producer = signed_by

    def start(self):
        for _ in self.scanner.scan():
            print('')

    def get_producer_from_line(self, line):
        match = re.search(r'(?<=signed by)(.*?)(?=\[)', line)
        if match:
            return match.group().strip()

    def get_rotations_object(self):
        conn = client.HTTPConnection(self.connect_string, 8888)
        body = {'scope': 'eosio', 'code': 'eosio', 'table': 'rotations', 'json': True}
        conn.request('POST', '/v1/chain/get_table_rows', json.dumps(body))
        response = conn.getresponse()
        return json.loads(response.read().decode('utf-8'))['rows'][0]

    def get_producer_schedule(self):
        conn = client.HTTPConnection(self.connect_string, 8888)
        body = {'json': True}
        conn.request('POST', '/v1/chain/get_producers', json.dumps(body))
        response = conn.getresponse()
        rotations = self.get_rotations_object()
        if response.status == 200:
            producers = json.loads(response.read().decode('utf-8'))
            schedule = []
            for p in producers['rows']:
                if rotations['bp_currently_out'] == p:
                    schedule.append(rotations['sbp_currently_in'])
                else:
                    schedule.append(p['owner'])
                if producers['rows'].index(p) >= 21:
                    break

            schedule = schedule[:21]
            schedule.sort()
            print('Retrieved Producer schedule ===============')
            print(schedule)
            return schedule
        return []
