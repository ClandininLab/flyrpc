import socket, json, sys

from queue import Queue, Empty
from threading import Event
from json.decoder import JSONDecodeError
from flyrpc.util import start_daemon_thread

class MyTransceiver:
    def __init__(self):
        # initialize variables
        self.functions = {}
        self.outfile = None
        self.queue = Queue()
        self.shutdown = Event()

    def handle_request_list(self, request_list):
        if not isinstance(request_list, list):
            return

        for request in request_list:
            if not isinstance(request, dict):
                continue

            if ('name' in request) and (request['name'] in self.functions):
                # get function call parameters
                function = self.functions[request['name']]
                args = request.get('args', [])
                kwargs = request.get('kwargs', {})

                # call function
                function(*args, **kwargs)

    def process_queue(self):
        while True:
            try:
                request_list = self.queue.get_nowait()
            except Empty:
                break

            self.handle_request_list(request_list)

    def register_function(self, function, name=None):
        if name is None:
            name = function.__name__

        assert name not in self.functions, 'Function "{}" already defined.'.format(name)
        self.functions[name] = function

    def __getattr__(self, name):
        def f(*args, **kwargs):
            request = {'name': name, 'args': args, 'kwargs': kwargs}
            self.write_request_list([request])

        return f

    def parse_line(self, line):
        return json.loads(line)

    def write_request_list(self, request_list):
        line = json.dumps(request_list) + '\n'
        line = line.encode('utf-8')

        try:
            self.outfile.write(line)
            self.outfile.flush()
        except AttributeError:
            # will happen if outfile is None
            pass
        except BrokenPipeError:
            # will happen if the other side disconnected
            pass


class MySocketClient(MyTransceiver):
    def __init__(self, host='127.0.0.1', port=0):
        super().__init__()

        conn = socket.create_connection((host, port))

        self.infile = conn.makefile('r')
        self.outfile = conn.makefile('wb')

        start_daemon_thread(self.loop)

    def loop(self):
        while True:
            line = self.infile.readline()

            try:
                request_list = self.parse_line(line)
            except JSONDecodeError:
                continue

            self.queue.put(request_list)


class MySocketServer(MyTransceiver):
    def __init__(self, host='127.0.0.1', port=0, threaded=True, auto_stop=False):
        super().__init__()

        # save settings
        self.threaded = threaded
        self.auto_stop = auto_stop

        # create the listener
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind((host, port))
        self.listener.listen()

        # print out socket information
        sockname = self.listener.getsockname()
        options = {'host': sockname[0], 'port': sockname[1]}
        options = json.dumps(options) + '\n'
        print(options)
        sys.stdout.flush()

        # launch the read thread
        if self.threaded:
            start_daemon_thread(self.loop)

    def loop(self):
        while not self.shutdown.is_set():
            conn, address = self.listener.accept()
            print('Accepted connection.')
            sys.stdout.flush()

            infile = conn.makefile('r')
            self.outfile = conn.makefile('wb')

            try:
                for line in infile:
                    try:
                        request_list = self.parse_line(line)
                    except JSONDecodeError:
                        continue

                    if self.threaded:
                        self.queue.put(request_list)
                    else:
                        self.handle_request_list(request_list)
            except ConnectionResetError:
                # for Windows error handling
                pass

            try:
                print('Dropped connection.')
                sys.stdout.flush()
            except OSError:
                pass

            if self.auto_stop:
                self.shutdown.set()