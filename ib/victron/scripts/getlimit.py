from serial import Serial
from ib.victron.mk2 import MK2

def main():
    port = Serial('/dev/ttyUSB0', 2400)
    mk2 = MK2(port)
    print mk2.master_multi_led_info()

    port.close()
