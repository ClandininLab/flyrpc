import sys

from jsonrpc import Dispatcher

from flyrpc.rpc import Transceiver
from flyrpc.streams import PipeIO

def echo(text):
    print('rx_pipe: ' + text)

def main():
    dispatcher = Dispatcher()
    dispatcher.add_method(echo)

    io = PipeIO(sys.stdin)
    Transceiver(io, dispatcher).process(blocking=True)

if __name__ == '__main__':
    main()