import sys
from serial import Serial
from ib.victron.mk2 import MK2

def main():
    port = Serial('/dev/ttyUSB0', 2400)
    mk2 = MK2(port)
    limit = float(sys.argv[1])
    mk2.set_assist(limit)
    port.close()
