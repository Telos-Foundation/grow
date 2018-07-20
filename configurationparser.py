import os
from json import dumps


class ConfigurationParser:

    def __init__(self):
        self.dict = {}

    def set(self, option, value):
        print('Option: %s Value: %s' % (str(option), str(value)))
        if option not in self.dict:
            self.dict[option] = []
        if len(self.dict[option]) == 0:
            self.dict[option].append(value)
        else:
            self.dict[option] = []
            self.dict[option].append(value)

    def append(self, option, value):
        if option not in self.dict:
            self.dict[option] = []
        for item in value:
            self.dict[option].append(item)

    def get(self, option):
        if option in self.dict:
            return self.dict[option].pop()
        return None

    def removeValue(self, option, value):
        try:
            if option in self.dict:
                self.dict[option].remove(value)
        except ValueError as e:
            print('Value not found')

    def removeAll(self, option):
        if option in self.dict:
            self.dict.pop(option, None)

    def read(self, path):
        if os.path.isfile(path):
            dict = {}
            with open(path, 'r') as f:
                for line in f:
                    equals = -1
                    pound = -1

                    if '#' in line:
                        pound = line.index('#')

                    if '=' in line:
                        equals = line.index('=')

                    if equals == -1 or (pound < equals and pound != -1):
                        continue
                    split = line.split('=')
                    option = split[0].strip()
                    value = split[1].strip()

                    if len(split) > 2:
                        value = split[1].strip() + '=' + split[2].strip()

                    if '#' in value:
                        value = value[0:value.index('#')]

                    if option not in dict:
                        dict[option] = []

                    dict[option].append(value)
            self.dict = dict



    def write(self, path):
        with open(path, 'w') as f:
            for key in self.dict:
                for value in self.dict[key]:
                    f.write('%s = %s\n' % (key, value))
            f.close()


    def __str__(self):
        return dumps(self.dict)