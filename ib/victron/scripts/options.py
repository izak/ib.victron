import sys
from argparse import ArgumentParser

def _options():
    parser = ArgumentParser(description=sys.argv[0])
    parser.add_argument("-p", "--port", action="store", type=str,
        default='/dev/ttyUSB0', help="Serial port for the MK2")
    parser.add_argument("-b", "--baudrate", action="store", type=int,
        default=2400,
        help="Baud rate for the MK2, usually 2400, which is also the default")
    return parser.parse_args()

class Options(object):
    def __init__(self, c):
        self.callback = c
        self.options = None

    def __getattr__(self, name):
        if self.options is None:
            self.options = self.callback()
        return getattr(self.options, name)

options = Options(_options)
