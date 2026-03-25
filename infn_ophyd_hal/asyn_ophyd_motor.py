"""
Standard EPICS asyn motor record Ophyd device.

Uses the standard EPICS motor record PV suffixes:
    .VAL (setpoint), .RBV (readback), .MSTA (status word),
    .DMOV (done moving), .VELO (velocity), .ACCL (acceleration),
    .HLM/.LLM (limits), .EGU (engineering units), etc.

This is the default motor class for ``devgroup='mot'`` unless a
specialised devtype (e.g. ``technosoft-asyn``, ``newport``, ``pollux``)
is registered.
"""

from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, EpicsMotor
from ophyd.status import MoveStatus
from .epik8s_device import epik8sDevice

import logging

logger = logging.getLogger(__name__)


class OphydAsynMotor(epik8sDevice, EpicsMotor):
    """Standard EPICS motor record device.

    Wraps ``ophyd.EpicsMotor`` with the ``epik8sDevice`` base so that
    it carries beamline config metadata (``iocname``, ``devtype``, etc.)
    and integrates with the :class:`DeviceFactory`.

    Component suffixes follow the EPICS motor record convention::

        PREFIX.VAL      user setpoint
        PREFIX.RBV      user readback
        PREFIX.MSTA     motor status word
        PREFIX.DMOV     done-moving flag
        PREFIX.VELO     velocity
        PREFIX.ACCL     acceleration time
        PREFIX.HLM      user high limit
        PREFIX.LLM      user low limit
        PREFIX.EGU      engineering units
        PREFIX.PREC     precision
        PREFIX.STOP     stop command
        PREFIX.HOMF     home forward
        PREFIX.HOMR     home reverse
    """

    # EpicsMotor already provides:
    #   user_readback, user_setpoint, velocity, acceleration,
    #   motor_egu, motor_stop, motor_done_move, direction_of_travel,
    #   high_limit_switch, low_limit_switch, etc.

    # Additional signals useful for diagnostics
    motor_prec = Cpt(EpicsSignalRO, '.PREC', kind='config')
    motor_hlm = Cpt(EpicsSignal, '.HLM', kind='config')
    motor_llm = Cpt(EpicsSignal, '.LLM', kind='config')

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, poi=None, **kwargs):
        kwargs.pop('config', None)
        if read_attrs is None:
            read_attrs = ['user_readback', 'user_setpoint']
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
        self.poi = poi


class OphydMotorSim:
    """In-memory simulated motor for testing without EPICS.

    Provides the same public interface as ``OphydAsynMotor`` /
    ``OphydTmlMotor`` but stores state in plain Python attributes.
    """

    def __init__(self, prefix='SIM', *, name='sim_motor', poi=None, **kwargs):
        self.prefix = prefix
        self.name = name
        self.poi = poi
        self._config = kwargs.get('config', None)
        self._position = 0.0
        self._setpoint = 0.0
        self._velocity = 1.0
        self._acceleration = 1.0
        self._moving = False
        self._homed = False
        self._egu = 'mm'
        self._precision = 3
        cfg = (self._config or {}).get('motor', {}) or {}
        self._low_limit = cfg.get('dllm', float('-inf'))
        self._high_limit = cfg.get('dhlm', float('inf'))

    # ------------------------------------------------------------------
    # Properties aligned with PositionerBase / EpicsMotor
    # ------------------------------------------------------------------

    @property
    def position(self):
        return self._position

    @property
    def moving(self):
        return self._moving

    @property
    def egu(self):
        return self._egu

    @property
    def limits(self):
        return (self._low_limit, self._high_limit)

    @property
    def precision(self):
        return self._precision

    # ------------------------------------------------------------------
    # Motion
    # ------------------------------------------------------------------

    def check_value(self, pos):
        low, high = self.limits
        if low != float('-inf') and pos < low:
            raise ValueError(f'{self.name} position {pos} below low limit {low}')
        if high != float('inf') and pos > high:
            raise ValueError(f'{self.name} position {pos} above high limit {high}')

    def move(self, position, wait=True, **kwargs):
        if isinstance(position, str):
            position = self.poi2pos(position)
        self.check_value(position)
        self._moving = True
        self._setpoint = position
        # Sim: instant move
        self._position = position
        self._moving = False
        return self

    def stop(self):
        self._moving = False

    def home(self, direction=1, wait=True, **kwargs):
        self._position = 0.0
        self._homed = True
        return self

    def set_current_position(self, pos):
        self._position = pos

    # ------------------------------------------------------------------
    # POI helpers
    # ------------------------------------------------------------------

    def poi2pos(self, poi_name):
        if self.poi:
            for k in self.poi:
                if poi_name == k['name']:
                    return k.get('pos', k.get('value', 0))
        return -1000

    def pos2poi(self, position, tolerance=10):
        if self.poi:
            for k in self.poi:
                p = k.get('pos', k.get('value', 0))
                if p - tolerance <= position <= p + tolerance:
                    return k['name']
        return ''

    def get_pos(self, poi=False):
        pos = self.position
        if poi:
            return {'pos': pos, 'name': self.pos2poi(pos)}
        return pos

    # ------------------------------------------------------------------
    # Stubs for ophyd Device interface
    # ------------------------------------------------------------------

    def read(self):
        return {self.name: {'value': self._position, 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}',
                            'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass
