import time

from flyrpc.rpc import Transceiver
from flyrpc.streams import ClientSocketIO

def main():
    transceiver = Transceiver(ClientSocketIO(host='127.0.0.1', port=54584))
    transceiver.echo('test')

    time.sleep(0.1)

if __name__ == '__main__':
    main()