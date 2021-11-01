from time import sleep
from datetime import datetime
from serial import Serial
from ib.victron.mk2 import MK2
from ib.victron.scripts.options import options

def main():
    port = Serial(options.port, options.baudrate, timeout=options.timeout)
    mk2 = MK2(port).start()

    try:
        while True:
            ac_info = mk2.ac_info()
            dc_info = mk2.dc_info()
            state = mk2.get_state()
            print('Time           ', datetime.now().strftime('%Y-%m-%d %H:%M'))
            print('--------------------------------')
            print('Inverter mode    ', state.capitalize())
            print('Mains Voltage    ', ac_info['umains'], 'V')
            print('AC output Voltage', ac_info['uinv'], 'V')
            print('Battery Voltage  ', dc_info['ubat'], 'V')
            print('Discharge current', dc_info['ibat'], 'A')
            print('DC Power draw    ', dc_info['ibat'] * dc_info['ubat'], 'W')
            print('AC Power draw    ', ac_info['uinv'] * ac_info['iinv'], 'VA')
            print('')
            sleep(5)
    except KeyboardInterrupt:
        pass
    port.close()
