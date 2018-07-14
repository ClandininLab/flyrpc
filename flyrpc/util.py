import sys
import subprocess
import os.path
import socket

def fullpath(path):
    return os.path.realpath(os.path.expanduser(path))

def python_subprocess(path, args=None, stdin=None, stdout=None, stderr=None):
    if args is None:
        args = []

    python = fullpath(sys.executable)

    return subprocess.Popen(args=[python, path]+args, stdin=stdin, stdout=stdout, stderr=stderr)

def make_server_socket(addr=('127.0.0.1', 0)):


    return listener