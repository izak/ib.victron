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

from struct import unpack, error as struct_error
from time import sleep
from threading import Thread, Lock

class DataObject(dict):
    """ An dictionary which allows you to also access data as attributes. """
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

class reify(object):
    """
    Put the result of a method which uses this (non-data)
    descriptor decorator in the instance dict after the first call,
    effectively replacing the decorator with an instance variable.
    """
    def __init__(self, wrapped): 
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except:
            pass
    def __get__(self, inst, objtype=None):
        if inst is None: 
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val

def D(d, data):
    print(d, ' '.join(['%02X' % x for x in data]))

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

class DummyContextManager(object):
    """ Context Manager that does nothing. So we can write code that
        optionally uses a context manager, """
    def __enter__(self):
        pass
    def __exit__(self, *args, **kwargs):
        return False

class MK2(object):
    """ Encapsulate the mk2 so we can query a Victron inverter. """

    def __init__(self, port, address=0):
        self.port = port
        self.address = address
        self.commslock = DummyContextManager()

    def start(self):
        # When nothing else is happening, we get a version response every
        # second. Once we start talking to the inverter it will stop
        # sending these gratuitous version responses for a while. To ensure our
        # serial port is synced, we send a request, then clear the buffer. This
        # shuts the inverter up for long enough to avoid a race condition.
        self.port.write(self.makeCommand('V'))
        sleep(0.5)
        self.port.reset_input_buffer()
        for i in range(0, 3):
            try:
                self.communicate('A', '\x01' + chr(self.address))
            except (ValueError, struct_error):
                pass
            else:
                break
        return self

    # Mains voltage
    @reify
    def _umains(self):
        data = self.communicate('W', '\x36\x00\x00')
        umains_scale, ignore, umains_offset = unpack('<h B h', data[3:8])
        return (umains_scale, umains_offset)

    @property
    def umains_scale(self):
        return self._umains[0]

    @property
    def umains_offset(self):
        return self._umains[1]

    # Mains current
    @reify
    def _imains(self):
        data = self.communicate('W', '\x36\x01\x00')
        imains_scale, ignore, imains_offset = unpack('<h B h', data[3:8])
        return (imains_scale, imains_offset)

    @property
    def imains_scale(self):
        return self._imains[0]

    @property
    def imains_offset(self):
        return self._imains[1]

    # Inverter voltage
    @reify
    def _uinv(self):
        data = self.communicate('W', '\x36\x02\x00')
        uinv_scale, ignore, uinv_offset = unpack('<h B h', data[3:8])
        return (uinv_scale, uinv_offset)

    @property
    def uinv_scale(self):
        return self._uinv[0]

    @property
    def uinv_offset(self):
        return self._uinv[1]

    # Inverter current
    @reify
    def _iinv(self):
        data = self.communicate('W', '\x36\x03\x00')
        iinv_scale, ignore, iinv_offset = unpack('<h B h', data[3:8])
        return (iinv_scale, iinv_offset)

    @property
    def iinv_scale(self):
        return self._iinv[0]

    @property
    def iinv_offset(self):
        return self._iinv[1]

    # Battery voltage
    @reify
    def _ubat(self):
        data = self.communicate('W', '\x36\x04\x00')
        ubat_scale, ignore, ubat_offset = unpack('<h B h', data[3:8])
        return (ubat_scale, ubat_offset)

    @property
    def ubat_scale(self):
        return self._ubat[0]

    @property
    def ubat_offset(self):
        return self._ubat[1]

    # Battery current
    @reify
    def _ibat(self):
        data = self.communicate('W', '\x36\x05\x00')
        ibat_scale, ignore, ibat_offset = unpack('<h B h', data[3:8])
        return (ibat_scale, ibat_offset)

    @property
    def ibat_scale(self):
        return self._ibat[0]

    @property
    def ibat_offset(self):
        return self._ibat[1]

    # Load
    @reify
    def _load(self):
        data = self.communicate('W', '\x36\x09\x00')
        load_scale, ignore, load_offset = unpack('<h B h', data[3:8])
        return (load_scale, load_offset)

    @property
    def load_scale(self):
        return self._load[0]

    @property
    def load_offset(self):
        return self._load[1]

    def makeCommand(self, command, data=''):
        length = len(command) + len(data) + 1
        buf = [length, 0xFF]
        buf.extend(map(ord, command))
        buf.extend(map(ord, data))
        checksum = 256 - sum(buf) % 256
        buf.append(checksum)
        return bytes(buf)

    def readResult(self):
        length_byte = self.port.read(1)

        if not len(length_byte):
            raise ValueError("No response length read from device")

        length = ord(length_byte)

        # Read l+1 bytes, +1 for the checksum
        data = self.port.read(length + 1)

        if len(data) != (length + 1):
            raise ValueError("Response from device did not match expected length")

        full_message = length_byte + data

        # Check checksum
        if sum([x for x in full_message])%256 != 0:
            D('<e', full_message)
            raise ValueError("Checksum failed")

        return data

    def communicate(self, cmd, params=''):
        v = self.makeCommand(cmd, params)
        with self.commslock:
            self.port.write(v)
            while True:
                data = self.readResult()
                if data[0] != 0xFF or data[1:2] != b'V':
                    # It's not a version frame
                    break
        return data

    def scale(self, factor):
        s = abs(factor)
        if s >= 0x4000:
            return 1.0/(0x8000 - s)
        return s

    def dc_info(self):
        data = self.communicate('F', '\x00')
        ubat = unpack('<H', data[6:8])[0]
        ibat = unpack('<i', data[8:11] + bytes([0x0] if data[10] < 0x80 else [0xff]))[0]
        icharge = unpack('<i', data[11:14] + bytes([0x0] if data[13] < 0x80 else [0xff]))[0]
        return DataObject({
            'ubat': (ubat+self.ubat_offset) * self.scale(self.ubat_scale),
            'ibat': (ibat+self.ibat_offset) * self.scale(self.ibat_scale),
            'icharge': (icharge+self.ibat_offset) * self.scale(self.ibat_scale)
        })

    def ac_info(self):
        # AC info
        data = self.communicate('F', '\x01')
        umains, imains, uinv, iinv = unpack(
            '<H h H h', data[6:14])
        u_f, i_f = unpack('<B B', data[1:3])
        return DataObject({
            'umains': (umains+self.umains_offset) * self.scale(self.umains_scale),
            'uinv': (uinv+self.uinv_offset) * self.scale(self.uinv_scale),
            'imains': (imains+self.imains_offset) * self.scale(self.imains_scale)*u_f,
            'iinv': (iinv+self.imains_offset) * self.scale(self.iinv_scale) * i_f
        })

    def master_multi_led_info(self):
        data = self.communicate('F', '\x05')
        min_limit, max_limit, limit = unpack('<H H H', data[6:12])

        return DataObject(
            min_limit=min_limit/10.0, max_limit=max_limit/10.0, limit=limit/10.0)

    def led_info(self):
        data = self.communicate('L')
        status = data[2]
        flash = data[3]
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
        state, substate = unpack('<B B', data[3:5])
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

    @property
    def version(self):
        """ This call is used specifically to ask for the version. That means
            we never need to query the version using communicate(), so if we
            ever receive a version response elsewhere, we can discard it.
        """
        v = self.makeCommand('V')
        with self.commslock:
            self.port.write(v)

            # Response will be
            # 1. <Length> 0xFF 'V' <d0> <d1> <d2> <d3> <mode> <Checksum>
            # Length will be 7 bytes. We need to read 9 bytes.
            data = self.port.read(9)

        # Check length and marker
        assert data[0] == 0x07
        assert data[1] == 0xFF
        assert data[2:3] == b'V'

        # Check checksum
        if sum([x for x in data])%256 != 0:
            D('<e', data)
            raise ValueError("Checksum failed")

        return unpack('<I', data[3:7])[0]

    def flush(self):
        """ Read and discard any data on the input line. """
        while self.port.inWaiting() > 0:
            try:
                data = self.readResult()
            except ValueError:
                # CRC error, better clear the buffer and get out of here.
                self.port.reset_input_buffer()
                break

            if data[0] != 0xFF or data[1:2] != b'V':
                D('discarded non-version frame', data)

class MK2Thread(Thread, MK2):
    """ Runs a background thread that continuously reads the serial port and
        discards version frames. """
    def __init__(self, *args, **kwargs):
        Thread.__init__(self)
        MK2.__init__(self, *args, **kwargs)
        self.running = False
        self.daemon = True
        self.commslock = Lock()

    def start(self):
        self.running = True
        MK2.start(self)
        Thread.start(self)
        return self

    def stop(self):
        self.running = False

    def run(self):
        """ If MK2Thread.start() is called, this will run in a separate thread.
            The idea is to keep reading the serial buffer in between commands
            so that any gratuitous responses (such as version frames) are
            removed (and optionally logged). Since the MultiPlus only sends
            version frames once a second or so, it should be sufficient if we
            wake up once a second to clean up.
        """
        while self.running:
            if self.commslock.acquire(False):
                try:
                    self.flush()
                finally:
                    self.commslock.release()
            sleep(1)
