# infn-ophyd-hal

**INFN Ophyd Hardware Abstraction Layer** — A Python library providing Ophyd device abstractions for hardware commonly used in INFN (Istituto Nazionale di Fisica Nucleare) facilities.

Current version: **2.14.0**

This package dramatically simplifies:
- **High-Level Scientific Applications** — Focus on physics, not hardware details
- **Generic IOC Implementation** — Reusable device interfaces across beamlines
- **GUI Development** — Consistent device APIs for control systems

## Overview

The library provides Ophyd-based device classes that abstract common hardware used in particle accelerators and beamlines. Each device class provides a uniform interface to interact with EPICS PVs, making it easy to integrate hardware into Python-based control systems.

All device classes inherit from the common base class `epik8sDevice`, ensuring consistent initialization patterns and standardised behaviour across all hardware abstractions.

### Key Features

- **Unified Device Interface** — All devices expose standard `get()` and `set()` methods
- **Ophyd Integration** — Built on the battle-tested Ophyd framework
- **EPICS Native** — Direct integration with EPICS control systems
- **Type-Safe** — Full type hints for better IDE support and code quality
- **Extensible** — Easy to add new device types via `DeviceFactory`
- **Simulation Support** — Every device group has a `*Sim` counterpart for offline testing
- **ChannelFinder integration** — Discover PV metadata without live IOCs
- **iocDefaults merging** — Template-based config inheritance from `values.yaml`

## Quick Start

```python
from infn_ophyd_hal import (
    OphydAsynMotor, OphydTmlMotor,
    OphydPSUnimag, ophyd_ps_state,
    SppOphydBpm,
    OphydRTD, OphydDI, OphydDO,
    OphydVPC,
)

# Standard asyn motor (Newport, Pollux etc.)
motor = OphydAsynMotor('SPARC:MOT:M1', name='m1',
                       poi=[{'name': 'YAG', 'pos': 50}])
motor.move(50.0, wait=True)
motor.move('YAG')

# TML motor
tml = OphydTmlMotor('SPARC:MOT:TML:GUNFLG01', name='gunflg01')
tml.move(688640, wait=True)

# Power supply
ps = OphydPSUnimag('SPARC:PS:MAG1', name='dipole')
ps.set_state(ophyd_ps_state.ON)
ps.set_current(5.0)

# BPM
bpm = SppOphydBpm('AC1BPM01', name='ac1bpm01')
print(f"x={bpm.x.get():.3f}  y={bpm.y.get():.3f}")

# I/O and temperature
if OphydDI('SPARC:IO:INTERLOCK', name='il').get():
    OphydDO('SPARC:IO:BEAM_EN', name='beam').set(1)
    print(OphydRTD('SPARC:TEMP:COOL1', name='cool').get(), '°C')
```

## Installation

### From PyPI (Recommended)

```bash
pip install infn-ophyd-hal
```

### From Source

```bash
git clone https://github.com/infn-epics/infn-ophyd-hal.git
cd infn-ophyd-hal
pip install -e .
```

### Docker

A Docker image is published to GHCR on every release tag. The default `CMD` runs the sim-device test suite:

```bash
docker pull ghcr.io/infn-epics/infn-ophyd-hal:<version>
docker run --rm ghcr.io/infn-epics/infn-ophyd-hal:<version>
```

## Device Classes

### Motor Devices

#### `OphydAsynMotor` — standard EPICS motor record *(default for `devgroup: mot`)*
Wraps `ophyd.EpicsMotor` with the `epik8sDevice` base.  
Used for all `devgroup: mot` IOCs unless a specialised `devtype` is set (e.g. `technosoft-asyn`, `newport`, `pollux` all resolve to this class except TML).

**PV suffixes (standard motor record):**

| Signal | Suffix | Access |
|---|---|---|
| User setpoint | `.VAL` | RW |
| User readback | `.RBV` | RO |
| Motor status | `.MSTA` | RO |
| Done moving | `.DMOV` | RO |
| Velocity | `.VELO` | RW |
| Acceleration | `.ACCL` | RW |
| High limit | `.HLM` | RW |
| Low limit | `.LLM` | RW |
| Engineering units | `.EGU` | RO |
| Precision | `.PREC` | RO |
| Stop | `.STOP` | WO |
| Home fwd/rev | `.HOMF` / `.HOMR` | WO |

**Example:**
```python
from infn_ophyd_hal import OphydAsynMotor

motor = OphydAsynMotor('SPARC:MOT:M1', name='m1',
                       poi=[{'name': 'sample', 'pos': 100}])

motor.move(100.0, wait=True)
print(motor.position)        # user readback
print(motor.egu)             # e.g. 'mm'
motor.move('sample')         # move to named POI
motor.stop()
```

#### `OphydTmlMotor` — Technosoft TML motor (`devtype: technosoft-asyn`)
Custom TML protocol with non-standard PV layout.

**PV suffixes:**

| Signal | Suffix |
|---|---|
| Position readback | `:RBV` |
| Position setpoint | `:VAL_SP` |
| Motor status word | `:MSTA` |
| Moving bit | `:MSTA.BA` |
| Velocity | `:VELO_SP` |
| Acceleration | `:ACCL_SP` |
| Jog velocity | `:JVEL_SP` |
| Home velocity | `:HVEL_SP` |

Soft limits are read from `config.motor.dllm` / `config.motor.dhlm`.

**Example:**
```python
from infn_ophyd_hal import OphydTmlMotor

motor = OphydTmlMotor('SPARC:MOT:TML:GUNFLG01', name='gunflg01',
                      poi=[{'name': 'YAG', 'value': 688640}],
                      config={'motor': {'dllm': -1e9, 'dhlm': 1e9}})

motor.move(688640, wait=True)
motor.home()
motor.move('YAG')   # named POI
```

#### `OphydMotorSim` — in-memory motor (`devtype: sim`)
No EPICS connection required. Full interface: `move()`, `stop()`, `home()`, `limits`, `position`, `egu`, `precision`, `poi2pos()`, `pos2poi()`, `get_pos()`, `read()`, `describe()`.

```python
from infn_ophyd_hal import OphydMotorSim

motor = OphydMotorSim(name='test_motor',
                      poi=[{'name': 'home', 'pos': 0}],
                      config={'motor': {'dllm': -200, 'dhlm': 200}})
motor.move(50.0)
assert motor.position == 50.0
motor.check_value(300)   # raises ValueError — out of limits
```

---

### Power Supply Devices

All classes share the `OphydPS` base and are registered via `PowerSupplyFactory`.

#### `OphydPS` — abstract base class
Methods: `get_current()`, `set_current(value)`, `get_state()`, `set_state(state: ophyd_ps_state)`.

#### `OphydPSDante` — Dante magnet supply (`devtype: dante`)

```python
from infn_ophyd_hal import OphydPSDante

dante = OphydPSDante('SPARC:PS:DANTE1', name='dante1')
dante.set_current(10.0)
print(dante.get_state())
```

#### `OphydPSUnimag` — UniMag / Hazemeyer supply (`devtype: unimag`, `haz-ser`)

```python
from infn_ophyd_hal import OphydPSUnimag, ophyd_ps_state

ps = OphydPSUnimag('SPARC:PS:MAG1', name='dipole')
ps.set_state(ophyd_ps_state.ON)
ps.set_current(7.5)
print(ps.get_state_name())   # 'ON'
```

#### `OphydPSSim` — simulated power supply (`devtype: sim`)
Thread-based simulation with configurable `slope` (A/s), `uncertainty_percentage`, `error_prob`, `interlock_prob`.

```python
from infn_ophyd_hal import OphydPSSim, ophyd_ps_state

ps = OphydPSSim(name='ps_sim', slope=10, simcycle=0.1)
ps.set_state(ophyd_ps_state.ON)
ps.set_current(5.0)
```

---

### Diagnostic Devices

#### `SppOphydBpm` — Libera SPP/SPPP BPM (`devtype: bpm`, `libera-sppp`)

**PV suffixes:**

| Signal | Suffix |
|---|---|
| Horizontal position | `:SA:SA_X_MONITOR` |
| Vertical position | `:SA:SA_Y_MONITOR` |
| Antenna A–D | `:SA:SA_[A-D]_MONITOR` |
| Sum | `:SA:SA_SUM_MONITOR` |
| Pulse counter | `:SA:SA_COUNTER_MONITOR` |
| Threshold setpoint | `:ENV:ENV_ADCSP_THRESHOLD_SP` |

**Example:**
```python
from infn_ophyd_hal import SppOphydBpm

bpm = SppOphydBpm('AC1BPM01', name='ac1bpm01')
print(bpm.x.get(), bpm.y.get(), bpm.sum.get())
bpm.thsld(300)    # set ADC threshold
bpm.reset()       # reset pulse counter
```

#### `OphydBpmSim` — simulated BPM (`devtype: sim`)
Returns Gaussian-distributed x/y values; `thsld()` and `reset()` update internal state.

---

### Vacuum Devices

#### `OphydVPC` — Agilent IPC Mini ion pump (`devtype: ipcmini`)
PV: `:PRES_RB`

#### `OphydVGC` — Pfeiffer TPG gauge (`devtype: tpg300`)
PV: `:PRES_RB`

**Example:**
```python
from infn_ophyd_hal import OphydVPC, OphydVGC

vpc = OphydVPC('SPARC:VAC:GUNVPC:GUNSIP01', name='gunsip01')
vgc = OphydVGC('SPARC:VAC:GUNVGC:GUNVGA01', name='gunvga01')
print(f"Ion pump: {vpc.get():.2e} mbar")
print(f"Penning:  {vgc.get():.2e} mbar")
```

#### Sim variants: `OphydVPCSim`, `OphydVGCSim`

---

### I/O Devices

All IO classes use `get()` for inputs and `get()` / `set(value)` for outputs.

| Class | PV suffix | Direction | Sim class |
|---|---|---|---|
| `OphydDI` | `:DI` | RO | `OphydDISim` |
| `OphydDO` | `:DO` | RW | `OphydDOSim` |
| `OphydAI` | `:AI` | RO | `OphydAISim` |
| `OphydAO` | `:AO` | RW | `OphydAOSim` |
| `OphydRTD` | `:TEMP` | RO | `OphydRTDSim` |

**Example:**
```python
from infn_ophyd_hal import OphydDI, OphydDO, OphydAO, OphydRTD

interlock = OphydDI('SPARC:IO:INTERLOCK', name='il')
beam_en   = OphydDO('SPARC:IO:BEAM_EN',   name='beam')
hv_sp     = OphydAO('SPARC:HV:PLAVOLT01', name='hv')
cooling   = OphydRTD('SPARC:TEMP:COOL1',  name='cool')

if interlock.get():
    beam_en.set(1)
    hv_sp.set(3.14)
    print(cooling.get(), '°C')
```

---

## Device Factory

`DeviceFactory` creates device instances from a `values.yaml` config file, resolving `devgroup`/`devtype` pairs to the correct class.

### Registered type map

| `devgroup` | `devtype` | Class |
|---|---|---|
| `mot` | `asyn`, `generic`, `motor`, `newport`, `pollux` | `OphydAsynMotor` |
| `mot` | `technosoft-asyn`, `tml` | `OphydTmlMotor` |
| `mot` | `sim` | `OphydMotorSim` |
| `vac` | `ipcmini` | `OphydVPC` |
| `vac` | `tpg300` | `OphydVGC` |
| `vac` | `sim` | `OphydVPCSim` |
| `diag` | `bpm`, `libera-spe`, `libera-sppp` | `SppOphydBpm` |
| `diag` | `sim` | `OphydBpmSim` |
| `mag` | `dante` | `OphydPSDante` |
| `mag` | `unimag`, `generic`, `haz-ser` | `OphydPSUnimag` |
| `mag` | `sim` | `OphydPSSim` |
| `io` | `di`, `do`, `ai`, `ao`, `rtd` | IO classes |
| `io` | `sim-di`, `sim-do`, `sim-ai`, `sim-ao`, `sim-rtd` | Sim IO classes |

Falls back to `(devgroup, 'generic')` if the exact devtype is not found.

### Usage

```python
from infn_ophyd_hal import DeviceFactory, create_devices_from_beamline_config

# From YAML
devices = create_devices_from_beamline_config('values.yaml')
devices['GUNFLG01'].move(688640, wait=True)

# Filtered by group
motors = create_devices_from_beamline_config('values.yaml', devgroup='mot')
bpms   = create_devices_from_beamline_config('values.yaml', devgroup='diag',
                                              name_pattern=r'^AC\d+BPM')

# Direct factory
factory = DeviceFactory()
device = factory.create_device('mot', 'sim', 'SIM:MOT', 'my_motor')

# Add a custom type at runtime
from my_module import MySpecialMotor
factory.register_device_type('mot', 'my-special', MySpecialMotor)
```

### Available filters for `create_devices_from_beamline_config`

| Parameter | Description |
|---|---|
| `name_pattern` | Regex matched against device name (case-insensitive) |
| `devgroup` | Exact match or regex against `devgroup` field |
| `devtype` | Exact match or regex against `devtype` field |
| `**kwargs` | Any config key, e.g. `zone='LINAC'` |

---

## ChannelFinder Client

```python
from infn_ophyd_hal import ChannelFinderClient

cf = ChannelFinderClient('http://channelfinder.example.com:8080/ChannelFinder')

if cf.is_available():
    channels = cf.search('SPARC:MOT:*')
    by_ioc   = cf.get_channels_by_ioc('tml-ch1')
    pvs      = cf.discover_devices()
```

---

## Simulation & Testing

Every device group has a `*Sim` class that runs without EPICS. A full pytest suite is included:

```bash
pip install pytest
pytest tests/test_sim_devices.py -v    # 43 tests, no IOC needed
```

Run the same suite inside Docker:

```bash
docker run --rm ghcr.io/infn-epics/infn-ophyd-hal:<version>
```

---

## Development

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e .
pip install pytest black flake8

# Tests (no EPICS required)
pytest tests/test_sim_devices.py -v

# Formatting / linting
black infn_ophyd_hal/
flake8 infn_ophyd_hal/
```

## CI/CD

GitHub Actions workflow (`.github/workflows/publish.yml`):

| Trigger | Jobs |
|---|---|
| Push to `main` | `sim-tests` → `pypi-publish` |
| Tag `v*` | `sim-tests` → `pypi-publish` + `docker-publish` (→ GHCR) |
| `workflow_dispatch` | `sim-tests` + `docker-publish` |

Required secrets: `PYPI_USERNAME`, `PYPI_TOKEN`.  
Docker auth uses the built-in `GITHUB_TOKEN`.

## Architecture

```
ophyd.Device
    └── epik8sDevice                        ← common base (prefix, config, _config)
            ├── OphydAsynMotor              (+ ophyd.EpicsMotor)
            ├── OphydTmlMotor               (+ ophyd.PositionerBase)
            ├── SppOphydBpm
            ├── OphydVPC / OphydVGC
            ├── OphydDI / DO / AI / AO / RTD
            └── OphydPS
                    ├── OphydPSDante
                    ├── OphydPSUnimag
                    └── OphydPSSim          ← threaded simulation

Pure-Python sim classes (no ophyd.Device):
    OphydMotorSim, OphydBpmSim,
    OphydDISim, OphydDOSim, OphydAISim, OphydAOSim, OphydRTDSim,
    OphydVPCSim, OphydVGCSim
```

### Extending

```python
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from infn_ophyd_hal.epik8s_device import epik8sDevice

class OphydMyDevice(epik8sDevice):
    readback = Cpt(EpicsSignalRO, ':RB')
    setpoint = Cpt(EpicsSignal,   ':SP')

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name,
                         read_attrs=['readback'], **kwargs)

    def get(self):
        return self.readback.get()

    def set(self, value):
        return self.setpoint.set(value)
```

Register it:

```python
# in __init__.py
from .my_device import OphydMyDevice

# at runtime
factory.register_device_type('mygroup', 'mytype', OphydMyDevice)
```

## Support and Contributing

- **Issues**: [GitHub Issues](https://github.com/infn-epics/infn-ophyd-hal/issues)
- **Pull Requests**: Contributions welcome!

## License

MIT — see `LICENSE`.

## Authors

Andrea Michelotti — INFN EPICS Team

## Acknowledgments

Built on the excellent [Ophyd](https://github.com/bluesky/ophyd) framework from the Bluesky project at NSLS-II.



