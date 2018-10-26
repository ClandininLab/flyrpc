import socket, json, atexit

from queue import Queue, Empty
from threading import Event
from json.decoder import JSONDecodeError

from flyrpc.util import start_daemon_thread, stream_is_binary

class MyTransceiver:
    def __init__(self):
        # initialize variables
        self.functions = {}
        self.outfile = None
        self.queue = Queue()

        # create shutdown flag
        self.shutdown_flag = Event()

        # create shutdown function
        def shutdown():
            self.shutdown_flag.set()

        # register shutdown function
        self.register_function(shutdown)

    def handle_request_list(self, request_list):
        if not isinstance(request_list, list):
            return

        for request in request_list:
            if isinstance(request, dict) and ('name' in request) and (request['name'] in self.functions):
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
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        return json.loads(line)

    def write_request_list(self, request_list):
        if self.outfile is None:
            return

        line = json.dumps(request_list) + '\n'

        if stream_is_binary(self.outfile):
            line = line.encode('utf-8')

        try:
            self.outfile.write(line)
            self.outfile.flush()
        except BrokenPipeError:
            # will happen if the other side disconnected
            pass


class MySocketClient(MyTransceiver):
    def __init__(self, host=None, port=None):
        super().__init__()

        # set defaults
        if host is None:
            host = '127.0.0.1'

        assert port is not None, 'The port must be specified when creating a client.'

        conn = socket.create_connection((host, port))

        # make sure that connection is closed on
        def cleanup():
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except (OSError, ConnectionResetError):
                pass

        atexit.register(cleanup)

        self.infile = conn.makefile('r')
        self.outfile = conn.makefile('wb')

        start_daemon_thread(self.loop)

    def loop(self):
        try:
            for line in self.infile:
                try:
                    request_list = self.parse_line(line)
                except JSONDecodeError:
                    continue

                self.queue.put(request_list)
        except (OSError, ConnectionResetError):
            pass


class MySocketServer(MyTransceiver):
    def __init__(self, host=None, port=None, threaded=None, auto_stop=None, accept_timeout=None, name=None):
        super().__init__()

        # set defaults
        if host is None:
            host = '127.0.0.1'

        if port is None:
            port = 0

        if threaded is None:
            threaded = True

        if auto_stop is None:
            auto_stop = True

        if accept_timeout is None:
            if auto_stop:
                accept_timeout = 10

        if name is None:
            name = self.__class__.__name__

        # save settings
        self.threaded = threaded
        self.auto_stop = auto_stop
        self.name = name

        # create the listener
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind((host, port))
        self.listener.listen()
        self.listener.settimeout(accept_timeout)

        # print out socket information
        sockname = self.listener.getsockname()
        print('{} hostname: {}'.format(self.name, sockname[0]))
        print('{} port: {}'.format(self.name, sockname[1]))

        # launch the read thread
        if self.threaded:
            start_daemon_thread(self.loop)

    def loop(self):
        while not self.shutdown_flag.is_set():
            # wait for connection
            try:
                conn, address = self.listener.accept()
            except socket.timeout:
                print('Server received no connection within timeout, shutting down...')
                break

            print('{} accepted connection.'.format(self.name))

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
            except (OSError, ConnectionResetError):
                pass

            print('{} dropped connection.'.format(self.name))

            if self.auto_stop:
                self.shutdown_flag.set()