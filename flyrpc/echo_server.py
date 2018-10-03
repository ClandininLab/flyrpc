from flyrpc.transceiver import MySocketServer

def echo(stuff):
    with open('test.txt', 'w') as f:
        f.write('echo: {}\n'.format(stuff))
        f.flush()

def main():
    server = MySocketServer(threaded=False, auto_stop=True)
    server.register_function(echo)
    server.loop()

if __name__ == '__main__':
    main()