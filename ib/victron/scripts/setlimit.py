import sys
from serial import Serial
from ib.victron.mk2 import MK2
from ib.victron.scripts.options import parser, options

def main():
    parser.add_argument("-l", "--limit", action="store", type=float,
        default=None, help="PowerAssist limit in Ampere")

    if options.limit is None:
        parser.print_help()
        sys.exit(1)

    port = Serial(options.port, options.baudrate)
    mk2 = MK2(port)
    mk2.set_assist(options.limit)
    port.close()
