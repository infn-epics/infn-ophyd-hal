# infn_ophyd_hal/motor.py

from ophyd import PositionerBase, DisconnectedError
from ophyd.utils.epics_pvs import raise_if_disconnected

from ophyd import Component as Cp
from .epik8s_device import epik8sDevice
from abc import ABC, abstractmethod



class ophyMotor(epik8sDevice, PositionerBase):
    '''An EPICS motor record, wrapped in a :class:`Positioner`

    Keyword arguments are passed through to the base class, Positioner

    Parameters
    ----------
    prefix : str
        The record to use
    read_attrs : sequence of attribute names
        The signals to be read during data acquisition (i.e., in read() and
        describe() calls)
    name : str, optional
        The name of the device
    parent : instance or None
        The instance of the parent device, if applicable
    settle_time : float, optional
        The amount of time to wait after moves to report status completion
    timeout : float, optional
        The default timeout to use for motion requests, in seconds.
    '''
    
    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = []
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

        

    @property
    @raise_if_disconnected
    @abstractmethod
    def precision(self):
        '''The precision of the readback PV, as reported by EPICS'''
        pass
    
    @property
    @raise_if_disconnected
    @abstractmethod

    def egu(self):
        '''The engineering units (EGU) for a position'''
        pass

    @property
    @raise_if_disconnected
    @abstractmethod

    def limits(self):
        pass

    @property
    @raise_if_disconnected
    @abstractmethod

    def moving(self):
        '''Whether or not the motor is moving

        Returns
        -------
        moving : bool
        '''
        pass

    @raise_if_disconnected
    @abstractmethod
    def stop(self):
        pass

    @raise_if_disconnected
    @abstractmethod

    def move(self, position, wait=True, **kwargs):
        '''Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.

        Returns
        -------
        status : MoveStatus

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        ValueError
            On invalid positions
        RuntimeError
            If motion fails other than timing out
        '''
        pass


    @property
    @raise_if_disconnected
    @abstractmethod
    def position(self):
       pass

    @raise_if_disconnected
    @abstractmethod

    def set_current_position(self, pos):
        '''Configure the motor user position to the given value

        Parameters
        ----------
        pos
           Position to set.

        '''
        pass


    @raise_if_disconnected
    @abstractmethod

    def home(self, direction, wait=True, **kwargs):
        '''Perform the default homing function in the desired direction

        Parameters
        ----------
        direction : HomeEnum
           Direction in which to perform the home search.
        '''
        pass

    @abstractmethod
    def check_value(self, pos):
        '''Check that the position is within the soft limits'''
        pass


    @property
    def report(self):
        try:
            rep = super().report
        except DisconnectedError:
            # TODO there might be more in this that gets lost
            rep = {'position': 'disconnected'}
        rep['pv'] = self.user_readback.pvname
        return rep



