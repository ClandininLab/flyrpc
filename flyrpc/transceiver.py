import socket, json, sys

from queue import Queue, Empty
from flyrpc.util import start_daemon_thread

class MyTransceiver:
    def __init__(self, input_binary=False, output_binary=True, line_ending='\n'):
        # save settings
        self.input_binary = input_binary
        self.output_binary = output_binary
        self.line_ending = line_ending

        # initialize variables
        self.functions = {}
        self.queue = Queue()
        self.infile = None
        self.outfile = None

        # special shutdown function
        self.should_run = True
        def shutdown():
            self.should_run = False
        self.register_function(shutdown)

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

    def serve_forever(self):
        while self.should_run:
            request_list = self.queue.get()
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
        if self.input_binary:
            line = line.decode('utf-8')

        line = line.strip()

        if line:
            data = json.loads(line)
            self.queue.put(data)

    def write_request_list(self, request_list):
        line = json.dumps(request_list)
        line += self.line_ending

        if self.output_binary:
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

    def start_read_thread(self):
        def target():
            while True:
                line = self.infile.readline()
                self.parse_line(line)

        start_daemon_thread(target)


class MySocketClient(MyTransceiver):
    def __init__(self, host='127.0.0.1', port=0):
        super().__init__()

        conn = socket.create_connection((host, port))

        self.infile = conn.makefile('r')
        self.outfile = conn.makefile('wb')

        self.start_read_thread()


class MySocketServer(MyTransceiver):
    def __init__(self, host='127.0.0.1', port=0, auto_stop=True):
        super().__init__()

        # save settings
        self.auto_stop = auto_stop

        # create the listener
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind((host, port))
        self.listener.listen()

        # print out socket information
        sockname = self.listener.getsockname()
        print('ServerAddress: ({}, {})'.format(sockname[0], sockname[1]))
        sys.stdout.flush()

        # launch the read thread
        self.start_read_thread()

    def start_read_thread(self):
        def target():
            while True:
                conn, address = self.listener.accept()
                print('Accepted connection.')
                sys.stdout.flush()

                infile = conn.makefile('r')
                self.outfile = conn.makefile('wb')

                try:
                    for line in infile:
                        self.parse_line(line)
                except ConnectionResetError:
                    # for Windows error handling
                    pass

                try:
                    print('Dropped connection.')
                    sys.stdout.flush()
                except OSError:
                    pass

                if self.auto_stop:
                    self.should_run = False

        start_daemon_thread(target)