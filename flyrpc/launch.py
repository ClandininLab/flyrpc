import sys, subprocess, os.path, re

from flyrpc.transceiver import MySocketClient

def fullpath(file):
    return os.path.realpath(os.path.expanduser(file))

def launch_server(module, *args, **kwargs):
    python = fullpath(sys.executable)
    path = fullpath(module.__file__)

    arg_list = []
    arg_list += [str(arg) for arg in args]
    arg_list += ['--{} {}'.format(str(k), str(v)) for k,v in kwargs.items()]

    proc = subprocess.Popen(args=[python, path]+arg_list, stdout=subprocess.PIPE)

    # set up pattern matching for port
    pattern = re.compile('ServerAddress: \(([\.\da-zA-Z]+), (\d+)\)')

    while True:
        line = proc.stdout.readline()
        line = line.decode('utf-8')
        line = line.strip()

        match = pattern.match(line)
        if match is not None:
            port = int(match.groups(0)[1])
            print('found port: {}'.format(port))
            return MySocketClient(port=port)