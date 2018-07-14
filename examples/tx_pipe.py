import subprocess
import sys
import time

import rx_pipe

from flyrpc.rpc import Transceiver
from flyrpc.streams import PipeIO
from flyrpc.util import fullpath, python_subprocess

def main():
    # get the full path of the server script
    p = python_subprocess(fullpath(rx_pipe.__file__), stdin=subprocess.PIPE, stdout=sys.stdout)

    transceiver = Transceiver(PipeIO(stdout=p.stdin))
    transceiver.echo('test')

    time.sleep(0.1)

    p.terminate()

if __name__ == '__main__':
    main()