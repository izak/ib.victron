from time import sleep
from datetime import datetime
from serial import Serial
from mk2 import MK2

port = Serial('/dev/ttyUSB0', 2400)
mk2 = MK2(port)

try:
    while True:
        ac_info = mk2.ac_info()
        dc_info = mk2.dc_info()
        led_info = mk2.led_info()
        print 'Time           ', datetime.now().strftime('%Y-%m-%d %H:%M')
        print '--------------------------------'
        print 'Inverter mode    ', led_info['inverter'] and 'Inverting' or 'Mains'
        print 'Mains Voltage    ', ac_info['umains'], 'V'
        print 'AC output Voltage', ac_info['uinv'], 'V'
        print 'Battery Voltage  ', dc_info['ubat'], 'V'
        print 'Discharge current', dc_info['ibat'], 'A'
        print 'DC Power draw    ', dc_info['ibat'] * dc_info['ubat'], 'W'
        print 'AC Power draw    ', ac_info['uinv'] * ac_info['iinv'], 'VA'
        print ''
        sleep(5)
except KeyboardInterrupt:
    pass
port.close()
