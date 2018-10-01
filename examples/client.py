from time import sleep

import flyrpc.echo_server

from flyrpc.launch import launch_server
from flyrpc.multicall import MyMultiCall

def main():
    server = launch_server(flyrpc.echo_server)

    for k in range(10):
        group = MyMultiCall(server)
        group.echo(str(k))
        group()

        sleep(0.5)

    server.shutdown()

if __name__ == '__main__':
    main()