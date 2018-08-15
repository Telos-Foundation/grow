import json
import re
import subprocess
import threading
from utility import tail_iterator

class FeedScanner:

    def __init__(self, filepath):
        self.subscribers = {}
        self.filepath = filepath

    def subscribe(self, pattern, callback):
        if pattern not in self.subscribers:
            self.subscribers[pattern] = []
        self.subscribers[pattern].append(callback)

    def unsubscribe(self, pattern, callback):
        try:
            if pattern not in self.subscribers:
                return
            else:
                self.subscribers[pattern].remove(callback)
        except ValueError as e:
            raise e

    def scan(self):
        for line in tail_iterator(self.filepath):
            for pattern in self.subscribers:
                match = re.search(pattern, line)
                if match:
                    for callback in self.subscribers[pattern]:
                        callback(line)
            yield None #STATE OBJECT
