from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO


class OphydDI(Device):
    """Digital Input: read-only boolean/value at ':DI'."""
    user_readback = Cpt(EpicsSignalRO, ':DI')
    
    def get(self):
        """Get current digital input value."""
        return self.user_readback.get()


class OphydDO(Device):
    """Digital Output: writable boolean/value at ':DO'."""
    user_setpoint = Cpt(EpicsSignal, ':DO')
    
    def get(self):
        """Get current digital output value."""
        return self.user_setpoint.get()
    
    def set(self, value):
        """Set digital output value."""
        return self.user_setpoint.set(value)


class OphydAI(Device):
    """Analog Input: read-only float at ':AI'."""
    user_readback = Cpt(EpicsSignalRO, ':AI')
    
    def get(self):
        """Get current analog input value."""
        return self.user_readback.get()


class OphydAO(Device):
    """Analog Output: writable float at ':AO'."""
    user_setpoint = Cpt(EpicsSignal, ':AO')
    
    def get(self):
        """Get current analog output value."""
        return self.user_setpoint.get()
    
    def set(self, value):
        """Set analog output value."""
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
