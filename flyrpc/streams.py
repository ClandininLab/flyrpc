import socket
from threading import Thread, Lock
from queue import Queue

class IO:
    def __init__(self):
        self.read_queue = Queue()

        self.outfile_lock = Lock()
        self._outfile = None

    def readline(self, blocking=True):
        if blocking:
            return self.read_queue.get()
        else:
            return self.read_queue.get_nowait()

    @property
    def outfile(self):
        with self.outfile_lock:
            return self._outfile

    @outfile.setter
    def outfile(self, value):
        with self.outfile_lock:
            self._outfile = value

    def write(self, data):
        self.outfile.write(data)

    def flush(self):
        self.outfile.flush()

class ServerSocketIO(IO):
    def __init__(self, host='127.0.0.1', port=0):
        super().__init__()

        # create the listener
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind((host, port))
        listener.listen()

        # print out socket information
        sockname = listener.getsockname()
        print('Server address: ({}, {})'.format(*sockname))

        # launch thread to read input asynchronously
        def target():
            while True:
                server, _ = listener.accept()

                sf = server.makefile('rwb')
                self.outfile = sf

                for line in sf:
                    self.read_queue.put(line)

        t = Thread(target=target)
        t.daemon = True
        t.start()

class ClientSocketIO(IO):
    def __init__(self, host='127.0.0.1', port=0):
        super().__init__()

        # create the connection
        client = socket.create_connection((host, port))
        cf = client.makefile('rwb')
        self.outfile = cf

        # launch thread to read input asynchronously
        def target():
            for line in cf:
                self.read_queue.put(line)

        t = Thread(target=target)
        t.daemon = True
        t.start()

class PipeIO(IO):
    def __init__(self, stdin=None, stdout=None):
        super().__init__()

        self.outfile = stdout

        if stdin is not None:
            def target():
                for line in stdin:
                    self.read_queue.put(line)
            t = Thread(target=target)
            t.daemon = True
            t.start()