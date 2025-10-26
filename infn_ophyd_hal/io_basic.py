from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO


class OphydDI(Device):
    """Digital Input: read-only boolean/value at ':DI'."""
    user_readback = Cpt(EpicsSignalRO, ':DI')


class OphydDO(Device):
    """Digital Output: writable boolean/value at ':DO'."""
    user_setpoint = Cpt(EpicsSignal, ':DO')


class OphydAI(Device):
    """Analog Input: read-only float at ':AI'."""
    user_readback = Cpt(EpicsSignalRO, ':AI')


class OphydAO(Device):
    """Analog Output: writable float at ':AO'."""
    user_setpoint = Cpt(EpicsSignal, ':AO')

class OphydRTD(Device):
    """
    Simple RTD temperature device.

    Exposes a read-only temperature attribute at suffix ':TEMP'.

    Example PV layout for a device named 'ALAS0' with iocprefix 'SPARC:TEMP':
      SPARC:TEMP:ALAS0:TEMP
    """

    user_readback = Cpt(EpicsSignalRO, ':TEMP')
