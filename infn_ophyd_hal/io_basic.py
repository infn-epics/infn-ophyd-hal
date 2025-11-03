from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO
import logging


class OphydDI(Device):
    """Digital Input: read-only boolean/value at ':DI'."""
    user_readback = Cpt(EpicsSignalRO, ':DI_RB')
    
    def get(self):
        """Get current digital input value."""
        return self.user_readback.get()


class OphydDO(Device):
    """Digital Output: writable boolean/value at ':DO_SP'."""
    user_setpoint = Cpt(EpicsSignal, ':DO_SP')
    
    def get(self):
        """Get current digital output value."""
        return self.user_setpoint.get()
    
    def set(self, value):
        """Set digital output value."""
        logging.info(f"Setting {self.name} digital output to {value}")
        return self.user_setpoint.set(value)


class OphydAI(Device):
    """Analog Input: read-only float at ':AI_RB'."""
    user_readback = Cpt(EpicsSignalRO, ':AI_RB')
    
    def get(self):
        """Get current analog input value."""
        return self.user_readback.get()


class OphydAO(Device):
    """Analog Output: writable float at ':AO_SP'."""
    user_setpoint = Cpt(EpicsSignal, ':AO_SP')
    
    def get(self):
        """Get current analog output value."""
        return self.user_setpoint.get()
    
    def set(self, value):
        """Set analog output value."""
        logging.info(f"Setting {self.name} analog output to {value}")
        return self.user_setpoint.set(value)


class OphydRTD(Device):
    """
    Simple RTD temperature device.

    Exposes a read-only temperature attribute at suffix ':TEMP'.

    Example PV layout for a device named 'ALAS0' with iocprefix 'SPARC:TEMP':
      SPARC:TEMP:ALAS0:TEMP
    """

    user_readback = Cpt(EpicsSignalRO, ':TEMP')
    
    def get(self):
        """Get current temperature reading."""
        return self.user_readback.get()
