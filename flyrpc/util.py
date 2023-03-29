import sys, json

from collections import defaultdict
from socket import socket
from threading import Thread

def start_daemon_thread(target):
    t = Thread(target=target)
    t.daemon = True
    t.start()

def stream_is_binary(stream):
    return 'b' in stream.mode

def find_free_port(host=''):
    # ref: https://stackoverflow.com/a/36331860
    s = socket()
    s.bind((host, 0))
    name = s.getsockname()[1]
    s.close()
    return name

def get_kwargs():
    try:
        kwargs = json.loads(sys.argv[1])
    except:
        kwargs = {}

    return defaultdict(lambda: None, kwargs)

