from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from .epik8s_device import epik8sDevice

import logging

logger = logging.getLogger(__name__)


class SppOphydBpm(epik8sDevice):
    x = Cpt(EpicsSignalRO, ':SA:SA_X_MONITOR')
    y = Cpt(EpicsSignalRO, ':SA:SA_Y_MONITOR')
    va = Cpt(EpicsSignalRO, ':SA:SA_A_MONITOR')
    vb = Cpt(EpicsSignalRO, ':SA:SA_B_MONITOR')
    vc = Cpt(EpicsSignalRO, ':SA:SA_C_MONITOR')
    vd = Cpt(EpicsSignalRO, ':SA:SA_D_MONITOR')
    sum = Cpt(EpicsSignalRO, ':SA:SA_SUM_MONITOR')
    ths= Cpt(EpicsSignalRO, ':ENV:ENV_ADCSP_THRESHOLD_MONITOR')
    thsp= Cpt(EpicsSignal, ':ENV:ENV_ADCSP_THRESHOLD_SP')
    cnt= Cpt(EpicsSignalRO, ':SA:SA_COUNTER_MONITOR')
    resetCmd=Cpt(EpicsSignal,':ENV:ENV_RESET_COUNTER_CMD')
    def __init__(self, prefix, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None,poi=None, **kwargs):
        
            
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
    def thsld(self,val):
        self.thsp.put(val)
    
    def reset(self):
        self.resetCmd.put(1)
            
            