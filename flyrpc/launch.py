import sys, subprocess, os.path, json

from time import sleep, time

from flyrpc.transceiver import MySocketClient
from flyrpc.util import find_free_port

def fullpath(file):
    return os.path.realpath(os.path.expanduser(file))

def launch_server(module, new_env_vars=None, server_poll_timeout=10, server_poll_interval=0.1, **kwargs):
    # add python interpreter and file name to commande
    cmd = [fullpath(sys.executable), fullpath(module.__file__)]

    # define host if necessary
    if 'host' not in kwargs:
        kwargs['host'] = '127.0.0.1'

    # define port if necessary
    if 'port' not in kwargs:
        kwargs['port'] = find_free_port(kwargs['host'])

    # write options to process
    cmd += [json.dumps(kwargs)]

    # set the environment variables
    if new_env_vars is None:
        new_env_vars = {}
    env = os.environ.copy()
    env.update(new_env_vars)

    # launch process
    subprocess.Popen(args=cmd, env=env)

    # try to establish connecting to client
    server_poll_start = time()
    while (time() - server_poll_start) < server_poll_timeout:
        try:
            return MySocketClient(host=kwargs['host'], port=kwargs['port'])
        except ConnectionRefusedError:
            sleep(server_poll_interval)
    else:
        raise Exception('Could not connect to server.')