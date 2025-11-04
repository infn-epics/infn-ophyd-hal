from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from .epik8s_device import epik8sDevice
import logging


class OphydVPC(epik8sDevice):
    """Digital Input: read-only boolean/value at ':DI'."""
    user_readback = Cpt(EpicsSignalRO, ':PRES_RB')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()
    def get(self):
        """Get current digital input value."""
        return self.user_readback.get()

class OphydVGC(epik8sDevice):
    user_readback = Cpt(EpicsSignalRO, ':PRES_RB')

    def __init__(self, prefix, read_attrs=None, configuration_attrs=None, name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback']
        super().__init__(prefix, read_attrs=read_attrs, configuration_attrs=configuration_attrs, name=name, parent=parent, **kwargs)
        self.get()
    def get(self):
        return self.user_readback.get()
