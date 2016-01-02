import sys
from argparse import ArgumentParser

def _parser():
    p = ArgumentParser(description=sys.argv[0])
    p.add_argument("-p", "--port", action="store", type=str,
        default='/dev/ttyUSB0', help="Serial port for the MK2")
    p.add_argument("-b", "--baudrate", action="store", type=int,
        default=2400,
        help="Baud rate for the MK2, usually 2400, which is also the default")
    return p
parser = _parser()

class Options(object):
    def __init__(self, p):
        self.parser = p
        self.options = None

    def __getattr__(self, name):
        if self.options is None:
            self.options = self.parser.parse_args()
        try:
            return getattr(self.options, name)
        except AttributeError:
            raise AttributeError(name)

options = Options(parser)
