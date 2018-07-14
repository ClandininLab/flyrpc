from queue import Empty

from jsonrpc import JSONRPCResponseManager
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20BatchRequest

# This file contains a simple stream-based remote procedure call system
# The work is inspired by this StackOverflow post:
# https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python

def make_request(method, *args, **kwargs):
    """
    Returns a single JSON RPC 2.0 request.
    :param method: Name of the method.
    :param params: Positional or keyword arguments of the method
    """

    if args:
        if kwargs:
            raise ValueError('Cannot use both positional and keyword arguments.')
        else:
            params = args
    else:
        params = kwargs

    return JSONRPC20Request(method=method, params=params, is_notification=True)

class Transceiver:
    """
    This class is intended to be scheduled to run inside an event loop.  It launches a thread to store each line of
    the stream into a queue.  The lines are then processed as remote procedure calls according to the JSON RPC
    specification.
    """

    def __init__(self, io, dispatcher=None):
        self.io = io
        self.dispatcher = dispatcher

    def process(self, blocking=False):
        while True:
            try:
                request = self.io.readline(blocking)
            except Empty:
                break

            # strip whitespace from the request
            stripped = request.strip()

            # handle the request if it's not empty
            if stripped != '':
                JSONRPCResponseManager.handle(stripped, self.dispatcher)

    def write(self, *requests):
        batch = JSONRPC20BatchRequest(*requests)
        self.io.write((batch.json + '\n').encode('utf-8'))
        self.io.flush()

    def __getattr__(self, method):
        """
        Generic handling for RPC methods.
        """

        def f(*args, **kwargs):
            self.write(make_request(method, *args, **kwargs))

        return f

class MultiCall:
    def __init__(self, transceiver: Transceiver):
        self.transceiver = transceiver
        self.requests = []

    def __getattr__(self, method):
        def f(*args, **kwargs):
            self.requests.append(make_request(method, *args, **kwargs))

        return f

    def __call__(self):
        self.transceiver.write(*self.requests)