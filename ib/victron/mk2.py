# Basic format is
# 1. <Length> 0xFF <Command> <Data 0 > ... <Data n-1 > <Checksum>
# 2. <Length> is the number of bytes in the frame, excluding the length and
# checksum bytes.
# 3. If the MSB of <Length> is a 1, then this frame has LED status appended.
# 4. <Checksum> is computed such that the sum of all bytes in the frame
# (including the length and checksum) equals 0.
# 5.  if the last data byte of the frame is 0xFF, the frame must be padded with
# 0x00 (and <Length> incremented).

# Checksum = 256-((sum_of_bytes_excluding_checksum)%256)

from struct import unpack

class DataObject(dict):
    """ An dictionary which allows you to also access data as attributes. """
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

def D(d, data):
    print d, ' '.join(['%02X' % ord(x) for x in data])

states = {
    (0, 0): 'down',
    (1, 0): 'startup',
    (2, 0): 'off',
    (3, 0): 'slave',
    (4, 0): 'invert full',
    (5, 0): 'invert half',
    (6, 0): 'invert aes',
    (7, 0): 'assist',
    (8, 0): 'bypass',
    (9, 0): 'charge init',
    (9, 1): 'charge bulk',
    (9, 2): 'charge absorption',
    (9, 3): 'charge float',
    (9, 4): 'charge storage',
    (9, 5): 'charge repeated absorption',
    (9, 6): 'charge forced absorption',
    (9, 7): 'charge equalise',
    (9, 8): 'charge bulk stopped',
}

class MK2(object):
    """ Encapsulate the mk2 so we can query a Victron inverter. """

    def __init__(self, port):
        self.port = port

        # Calibrate
        # version
        data = self.communicate('V')

        # Select address zero
        data = self.communicate('A', '\x01\x00')

        # Get the scalings
        # UMainsRMS
        data = self.communicate('W', '\x36\x00\x00')
        self.umains_scale = unpack('<h', data[3:5])[0]
        self.umains_offset = unpack('<h', data[6:8])[0]

        # IMainsRMS
        data = self.communicate('W', '\x36\x01\x00')
        self.imains_scale = unpack('<h', data[3:5])[0]
        self.imains_offset = unpack('<h', data[6:8])[0]

        data = self.communicate('W', '\x36\x02\x00')
        self.uinv_scale = unpack('<h', data[3:5])[0]
        self.uinv_offset = unpack('<h', data[6:8])[0]

        data = self.communicate('W', '\x36\x03\x00')
        self.iinv_scale = unpack('<h', data[3:5])[0]
        self.iinv_offset = unpack('<h', data[6:8])[0]

        data = self.communicate('W', '\x36\x04\x00')
        self.ubat_scale = unpack('<h', data[3:5])[0]
        self.ubat_offset = unpack('<h', data[6:8])[0]

        data = self.communicate('W', '\x36\x05\x00')
        self.ibat_scale = unpack('<h', data[3:5])[0]
        self.ibat_offset = unpack('<h', data[6:8])[0]

        data = self.communicate('W', '\x36\x09\x00')
        self.load_scale = unpack('<h', data[3:5])[0]
        self.load_offset = unpack('<h', data[6:8])[0]

    def makeCommand(self, command, data=''):
        length = len(command) + len(data) + 1
        buf = [chr(length), chr(0xFF)]
        buf.extend(command)
        buf.extend(data)
        checksum = 256 - sum([ord(x) for x in buf])%256
        buf.append(chr(checksum))
        return ''.join(buf)

    def readResult(self):
        l = ord(self.port.read(1))

        # Read l+1 bytes, +1 for the checksum
        data = self.port.read(l+1)

        # Check checksum
        if sum([ord(x) for x in (data + chr(l))])%256 != 0:
            D('<e', chr(l) + data)
            raise ValueError("Checksum failed")

        return data

    def communicate(self, cmd, params=''):
        v = self.makeCommand(cmd, params)
        self.port.flushInput()
        self.port.write(v)
        data = self.readResult()
        return data

    def scale(self, factor):
        s = abs(factor)
        if s >= 0x4000:
            return 1.0/(0x8000 - s)
        return s

    def dc_info(self):
        data = self.communicate('F', '\x00')
        ubat = unpack('<H', data[6:8])[0]
        ibat = unpack('<i', data[8:11] + ('\0' if data[10] < '\x80' else '\xff'))[0]
        icharge = unpack('<i', data[11:14] + ('\0' if data[13] < '\x80' else '\xff'))[0]
        return DataObject({
            'ubat': (ubat+self.ubat_offset) * self.scale(self.ubat_scale),
            'ibat': (ibat+self.ibat_offset) * self.scale(self.ibat_scale),
            'icharge': (icharge+self.ibat_offset) * self.scale(self.ibat_scale)
        })

    def ac_info(self):
        # AC info
        data = self.communicate('F', '\x01')
        umains = unpack('<H', data[6:8])[0]
        imains = unpack('<h', data[8:10])[0]
        uinv = unpack('<H', data[10:12])[0]
        iinv = unpack('<h', data[12:14])[0]
        u_f = unpack('<B', data[1])[0]
        i_f = unpack('<B', data[2])[0]
        return DataObject({
            'umains': (umains+self.umains_offset) * self.scale(self.umains_scale),
            'uinv': (uinv+self.uinv_offset) * self.scale(self.uinv_scale),
            'imains': (imains+self.imains_offset) * self.scale(self.imains_scale)*u_f,
            'iinv': (iinv+self.imains_offset) * self.scale(self.iinv_scale) * i_f
        })

    def master_multi_led_info(self):
        data = self.communicate('F', '\x05')
        min_limit = unpack('<H', data[6:8])[0]
        max_limit = unpack('<H', data[8:10])[0]
        limit = unpack('<H', data[10:12])[0]
        return DataObject(
            min_limit=min_limit, max_limit=max_limit, limit=limit)

    def led_info(self):
        data = self.communicate('L')
        status = ord(data[2])
        flash = ord(data[3])
        return DataObject({
            'mains': bool(status & 1),
            'absorption': bool(status & 2),
            'bulk': bool(status & 4),
            'float': bool(status & 8),
            'inverter': bool(status & 16),
            'overload': bool(status & 32),
            'low bat': bool(status & 64),
            'temp': bool(status & 128),
        })

    def get_state(self):
        data = self.communicate('W', '\x0E\x00\x00')
        state = unpack('<B', data[3])[0]
        substate = unpack('<B', data[4])[0]
        return states[(state, substate)]

    def set_state(self, s):
        """ 1: forced equalise
            2: forced absorption
            3: forced float
        """
        assert s in (1, 2, 3), 'state must be between 1 and 3'
        self.communicate('W', '\x0E' + chr(s) + '\x00')

    def set_assist(self, a):
        """ Set the ampere level for PowerAssist. """
        a = int(a*10)
        lo = a&0xff
        hi = a>>8
        self.communicate('S', '\x03' + chr(lo) + chr(hi) + '\x01\x80')
