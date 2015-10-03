# Utilities to talk to a Victron inverter

This includes a simple library for the mk2 protocol, and some scripts for
talking to a Multiplus. Use at your own risk.

## MK2 class

The MK2 class takes a single argument, a serial port object from pyserial.
This is usually to /dev/ttyUSB0 with a baudrate of 2400. Upon construction,
all scaling and offset values are queried from the inverter so that later
operations need not query them again.

The other methods are discussed below.

* dc_info

    Returns a dict/object with these items:
        * ubat: Battery voltage
        * ibat: Battery discharge current
        * icharge: Battery charge current

* ac_info

    Returns a dict/object with:
        * umains: Mains voltage
        * uinv: Inverter output voltage
        * imains: Current on the AC input
        * iinv: Current on the inverter output

* master_multi_led_info

    Returns a dict/object with:
        * min_limit: Minimum powerassist level in ampere
        * max_limit: Maximum powerassist level supported by device, in ampere
        * limit: Current power-assist level

* led_info

    Returns a dict/object with True/False fields for leds:
            * mains
            * absorption
            * bulk
            * float
            * inverter
            * overload
            * low bat
            * temp
    
* get_state

    Returns text string indicating current state of inverter.

* set_state

    Takes an integer argument, set charger such that:

        * 1: forced equalise mode
        * 2: forced absorption mode
        * 3: forced float mode

* set_assist

    Takes a single argument, which is a floating point value indicating the
    PowerAssist level in ampere. If you set this lower than min_limit as
    returned by master_multi_led_info, it will assume the minimum. If you set
    it higher than max_limit in master_multi_led_info, it willa ssume the
    maximum. If you set it to zero, the inverter goes into invert mode.
