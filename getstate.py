from serial import Serial
from mk2 import MK2

port = Serial('/dev/ttyUSB0', 2400)
mk2 = MK2(port)

#mk2.set_state(2)
print mk2.get_state()

port.close()
