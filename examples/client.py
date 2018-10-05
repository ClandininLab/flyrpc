#!/usr/bin/env python3

import flyrpc.echo_server

from flyrpc.launch import launch_server

def main():
    client = launch_server(flyrpc.echo_server)
    client.echo('hi')

if __name__ == '__main__':
    main()
