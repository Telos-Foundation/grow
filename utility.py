import json
import os
import subprocess
import time
import sys
import random


def tail(path):
    f = subprocess.Popen(['tail', '-F', path], \
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = f.stdout.readline()
        print(line)


def jsonArg(a):
    return " '" + json.dumps(a) + "' "


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


def log_file(filename):
    f = open(filename, 'a')
    f.seek(0, os.SEEK_END)
    return f


def create_file(name, input):
    with open(name, "w") as f:
        f.write(str(input))
        f.close()


def delete_file(file):
    os.remove(file)


def run(args, isShell=True, show=True):
    if show:
        print(args)
    if subprocess.call(args, shell=isShell):
        print('exiting because of error')
        sys.exit(1)

def run_retry(args, isShell=True, num=1):
    print(args)
    o = subprocess.call(args, shell=isShell)
    if o and num <= 3:
        print('Failed retrying... ')
        time.sleep(5)
        run_retry(args, True, num + 1)
    elif o:
        print('exiting because of error')
        sys.exit(1)


def run_continue(args, isShell=True):
    print(args)
    if subprocess.call(args, shell=isShell):
        print('command failed')


def get_output(args):
    print(args)
    proc = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
    return proc.communicate()[0].decode('utf-8')


def start_background_proc(args, file, path='./nodeos.pid'):
    print(args)
    p = subprocess.Popen(args,
                         stdout=file,
                         stderr=file, shell=False)
    create_file(path, p.pid)


def background(args):
    return subprocess.Popen(args, shell=True)


def id_generator(size=4, chars='12345bcdefghijkmnoqrstuvwxyz'):
    tmp = chars
    value = ""
    for _ in range(size):
        t = random.choice(tmp)
        value += t
        tmp.replace(t, "")
    return value


def join(a, b):
    return os.path.join(a, b)
