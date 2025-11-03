from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from .epik8s_device import epik8sDevice
import logging


class OphydDI(epik8sDevice):
    """Digital Input: read-only boolean/value at ':DI'."""
    user_readback = Cpt(EpicsSignalRO, ':DI_RB')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()
    def get(self):
        """Get current digital input value."""
        return self.user_readback.get()


class OphydDO(epik8sDevice):
    """Digital Output: writable boolean/value at ':DO_SP'."""
    user_setpoint = Cpt(EpicsSignal, ':DO_SP')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_setpoint']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()


    def get(self):
        """Get current digital output value."""
        return self.user_setpoint.get()

    def set(self, value):
        """Set digital output value."""
        logging.info(f"Setting {self.name} digital output to {value}")
        return self.user_setpoint.put(value)


class OphydAI(epik8sDevice):
    """Analog Input: read-only float at ':AI_RB'."""
    user_readback = Cpt(EpicsSignalRO, ':AI_RB')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()


    def get(self):
        """Get current analog input value."""
        return self.user_readback.get()


class OphydAO(epik8sDevice):
    """Analog Output: writable float at ':AO_SP'."""
    user_setpoint = Cpt(EpicsSignal, ':AO_SP')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_setpoint']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()


    def get(self):
        """Get current analog output value."""
        return self.user_setpoint.get()

    def set(self, value):
        """Set analog output value."""
        logging.info(f"Setting {self.name} analog output to {value}")
        return self.user_setpoint.put(value)


class OphydRTD(epik8sDevice):
    """
    Simple RTD temperature device.

    Exposes a read-only temperature attribute at suffix ':TEMP'.

    Example PV layout for a device named 'ALAS0' with iocprefix 'SPARC:TEMP':
      SPARC:TEMP:ALAS0:TEMP
    """

    user_readback = Cpt(EpicsSignalRO, ':TEMP_RB')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()


    def get(self):
        """Get current temperature reading."""
        return self.user_readback.get()
