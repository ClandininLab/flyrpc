import flyrpc.echo_server

from flyrpc.launch import launch_server

def main():
    server = launch_server(flyrpc.echo_server)
    server.echo('hi')

if __name__ == '__main__':
    main()