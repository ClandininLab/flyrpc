import sys, subprocess, os.path, json

from json.decoder import JSONDecodeError
from flyrpc.transceiver import MySocketClient

def fullpath(file):
    return os.path.realpath(os.path.expanduser(file))

def launch_server(module, *args, **kwargs):
    python = fullpath(sys.executable)
    path = fullpath(module.__file__)

    proc = subprocess.Popen(args=[python, path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    # write options to process
    options = {'args': args, 'kwargs': kwargs}
    options = json.dumps(options) + '\n'
    options = options.encode('utf-8')
    proc.stdin.write(options)

    # read port from server
    while True:
        line = proc.stdout.readline()
        line = line.decode('utf-8')

        try:
            data = json.loads(line)
        except JSONDecodeError:
            continue

        try:
            port = data['port']
        except KeyError:
            continue

        print('Found port: {}'.format(port))
        return MySocketClient(port=port)