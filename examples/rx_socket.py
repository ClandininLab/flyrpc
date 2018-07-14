from jsonrpc import Dispatcher

from flyrpc.rpc import Transceiver
from flyrpc.streams import ServerSocketIO

def echo(text):
    print('rx_socket: ' + text)

def main():
    dispatcher = Dispatcher()
    dispatcher.add_method(echo)

    io = ServerSocketIO()
    Transceiver(io, dispatcher).process(blocking=True)

if __name__ == '__main__':
    main()