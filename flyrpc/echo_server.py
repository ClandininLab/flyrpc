from flyrpc.transceiver import MySocketServer

def echo(stuff):
    print('echo: {}'.format(stuff))

def main():
    server = MySocketServer()
    server.register_function(echo)
    server.serve_forever()

if __name__ == '__main__':
    main()