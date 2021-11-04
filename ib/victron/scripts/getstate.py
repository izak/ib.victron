from serial import Serial
from ib.victron.mk2 import MK2
from ib.victron.scripts.options import options

def main():
    port = Serial(options.port, options.baudrate, timeout=options.timeout)
    mk2 = MK2(port).start()

    #mk2.set_state(3)
    print(mk2.get_state())

    port.close()
