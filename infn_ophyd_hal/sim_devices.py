"""
Simulated device classes for testing without live EPICS IOCs.

Each sim class mirrors the public API of its real counterpart but stores
state in plain Python attributes.
"""

import logging
import random

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BPM Sim
# ---------------------------------------------------------------------------

class OphydBpmSim:
    """Simulated BPM — returns random beam position values."""

    def __init__(self, prefix='SIM', *, name='sim_bpm', **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._x = 0.0
        self._y = 0.0
        self._sum = 100.0
        self._threshold = 0.5

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def sum(self):
        return self._sum

    def read(self):
        self._x = random.gauss(0, 0.1)
        self._y = random.gauss(0, 0.1)
        return {
            f'{self.name}_x': {'value': self._x, 'timestamp': 0},
            f'{self.name}_y': {'value': self._y, 'timestamp': 0},
            f'{self.name}_sum': {'value': self._sum, 'timestamp': 0},
        }

    def thsld(self, val):
        self._threshold = val

    def reset(self):
        self._x = 0.0
        self._y = 0.0

    def describe(self):
        return {f'{self.name}_x': {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []},
                f'{self.name}_y': {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


# ---------------------------------------------------------------------------
# IO Sims
# ---------------------------------------------------------------------------

class OphydDISim:
    """Simulated Digital Input."""

    def __init__(self, prefix='SIM', *, name='sim_di', **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._value = 0

    def get(self):
        return self._value

    def set_sim_value(self, v):
        self._value = v

    def read(self):
        return {self.name: {'value': self._value, 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'integer', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


class OphydDOSim:
    """Simulated Digital Output."""

    def __init__(self, prefix='SIM', *, name='sim_do', **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._value = 0

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

    def read(self):
        return {self.name: {'value': self._value, 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'integer', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


class OphydAISim:
    """Simulated Analog Input."""

    def __init__(self, prefix='SIM', *, name='sim_ai', noise=0.01, **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._value = 0.0
        self._noise = noise

    def get(self):
        return self._value + random.gauss(0, self._noise)

    def set_sim_value(self, v):
        self._value = v

    def read(self):
        return {self.name: {'value': self.get(), 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


class OphydAOSim:
    """Simulated Analog Output."""

    def __init__(self, prefix='SIM', *, name='sim_ao', **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._value = 0.0

    def get(self):
        return self._value

    def set(self, value):
        self._value = float(value)

    def read(self):
        return {self.name: {'value': self._value, 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


class OphydRTDSim:
    """Simulated RTD temperature sensor."""

    def __init__(self, prefix='SIM', *, name='sim_rtd', base_temp=22.0, noise=0.05, **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._base_temp = base_temp
        self._noise = noise

    def get(self):
        return self._base_temp + random.gauss(0, self._noise)

    def read(self):
        return {self.name: {'value': self.get(), 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


# ---------------------------------------------------------------------------
# Vacuum Sims
# ---------------------------------------------------------------------------

class OphydVPCSim:
    """Simulated vacuum gauge (IPC Mini-style)."""

    def __init__(self, prefix='SIM', *, name='sim_vpc', base_pressure=1e-7, **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._base_pressure = base_pressure

    def get(self):
        return self._base_pressure * (1 + random.gauss(0, 0.02))

    def read(self):
        return {self.name: {'value': self.get(), 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass


class OphydVGCSim:
    """Simulated vacuum gauge (TPG300-style)."""

    def __init__(self, prefix='SIM', *, name='sim_vgc', base_pressure=1e-5, **kwargs):
        self.prefix = prefix
        self.name = name
        self._config = kwargs.get('config', None)
        self._base_pressure = base_pressure

    def get(self):
        return self._base_pressure * (1 + random.gauss(0, 0.03))

    def read(self):
        return {self.name: {'value': self.get(), 'timestamp': 0}}

    def describe(self):
        return {self.name: {'source': f'SIM:{self.prefix}', 'dtype': 'number', 'shape': []}}

    def stage(self):
        pass

    def unstage(self):
        pass
