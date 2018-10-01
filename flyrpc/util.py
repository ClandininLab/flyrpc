from threading import Thread

def start_daemon_thread(target):
    t = Thread(target=target)
    t.daemon = True
    t.start()