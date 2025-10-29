# infn-ophyd-hal

**INFN Ophyd Hardware Abstraction Layer** - A Python library providing Ophyd device abstractions for hardware commonly used in INFN (Istituto Nazionale di Fisica Nucleare) facilities.

This package dramatically simplifies:
- **High-Level Scientific Applications** - Focus on physics, not hardware details
- **Generic IOC Implementation** - Reusable device interfaces across beamlines
- **GUI Development** - Consistent device APIs for control systems

## Overview

The library provides Ophyd-based device classes that abstract common hardware used in particle accelerators and beamlines. Each device class provides a uniform interface to interact with EPICS PVs, making it easy to integrate hardware into Python-based control systems.

### Key Features

- **Unified Device Interface** - All devices expose standard `get()` and `set()` methods
- **Ophyd Integration** - Built on the battle-tested Ophyd framework
- **EPICS Native** - Direct integration with EPICS control systems
- **Type-Safe** - Full type hints for better IDE support and code quality
- **Extensible** - Easy to add new device types

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

## Device Classes

### Motor Devices

#### OphydTmlMotor
TML (Technosoft Motion Language) motor controller abstraction.

**PV Layout:**
- `:POS_RB` - Position readback (RO)
- `:POS_SP` - Position setpoint (RW)
- `:MOVING` - Moving status (RO)
- `:STOP` - Stop command (WO)

**Example:**
```python
from infn_ophyd_hal import OphydTmlMotor

# Create motor instance
motor = OphydTmlMotor('SPARC:MOTOR:X', name='x_motor')

# Read current position
position = motor.position()

# Move to new position
motor.move(10.5, wait=True)

# Check if moving
if motor.moving():
    print("Motor is moving...")

# Stop motor
motor.stop()
```

#### OphydMotor
Generic motor abstraction for standard EPICS motor records.

**Methods:**
- `position()` - Get current position
- `move(value, wait=False)` - Move to position
- `stop()` - Stop motion

### Power Supply Devices

#### OphydPS (Base Power Supply)
Generic power supply with current control.

**PV Layout:**
- `:CURRENT_RB` - Current readback (RO)
- `:CURRENT_SP` - Current setpoint (RW)

**Example:**
```python
from infn_ophyd_hal import OphydPS

ps = OphydPS('SPARC:PS:MAG1', name='magnet1')
current = ps.get_current()
ps.set_current(5.0)
```

#### OphydPSDante
Dante magnet power supply with advanced features.

**PV Layout:**
- `:CURRENT_RB`, `:CURRENT_SP` - Current control
- `:STATE_RB`, `:STATE_SP` - State management
- Additional Dante-specific PVs

**Example:**
```python
from infn_ophyd_hal import OphydPSDante

dante = OphydPSDante('SPARC:PS:DANTE1', name='dante_magnet')
dante.set_current(10.0)
state = dante.get_state()
```

#### OphydPSUnimag
UniMag power supply abstraction.

**State Mapping:**
- 0: OFF
- 1: STANDBY
- 2: ON
- 3: FAULT

**Example:**
```python
from infn_ophyd_hal import OphydPSUnimag

unimag = OphydPSUnimag('SPARC:PS:UNIMAG1', name='unimag1')

# Set current
unimag.set_current(7.5)

# Control state
unimag.set_state(2)  # Turn ON

# Read mapped state
state_name = unimag.get_state_name()  # Returns 'ON'
```

#### OphydPSSim
Simulated power supply for testing and development.

### Diagnostic Devices

#### OphydBPM (Beam Position Monitor)
BPM device for beam diagnostics.

**PV Layout:**
- `:X`, `:Y` - Position readings
- `:INTENSITY` - Beam intensity
- Additional diagnostic PVs

**Example:**
```python
from infn_ophyd_hal import OphydBPM

bpm = OphydBPM('SPARC:DIAG:BPM1', name='bpm1')
x_pos = bpm.x.get()
y_pos = bpm.y.get()
intensity = bpm.intensity.get()
```

### I/O Devices

#### OphydDI (Digital Input)
Digital input device - read-only.

**PV:** `:DI`

**Example:**
```python
from infn_ophyd_hal import OphydDI

di = OphydDI('SPARC:IO:DI1', name='door_sensor')
is_open = di.get()  # Returns boolean
```

#### OphydDO (Digital Output)
Digital output device - read/write.

**PV:** `:DO`

**Example:**
```python
from infn_ophyd_hal import OphydDO

do = OphydDO('SPARC:IO:DO1', name='led_control')
current_state = do.get()
do.set(1)  # Turn on
do.set(0)  # Turn off
```

#### OphydAI (Analog Input)
Analog input device - read-only.

**PV:** `:AI`

**Example:**
```python
from infn_ophyd_hal import OphydAI

ai = OphydAI('SPARC:IO:AI1', name='voltage_sensor')
voltage = ai.get()  # Returns float
```

#### OphydAO (Analog Output)
Analog output device - read/write.

**PV:** `:AO`

**Example:**
```python
from infn_ophyd_hal import OphydAO

ao = OphydAO('SPARC:IO:AO1', name='voltage_control')
current_voltage = ao.get()
ao.set(3.14)  # Set voltage
```

#### OphydRTD (Temperature Sensor)
RTD (Resistance Temperature Detector) device.

**PV:** `:TEMP`

**Example:**
```python
from infn_ophyd_hal import OphydRTD

rtd = OphydRTD('SPARC:TEMP:RTD1', name='cooling_temp')
temperature = rtd.get()  # Returns temperature in configured units
```

## Quick Start Example

Here's a complete example using multiple device types:

```python
from infn_ophyd_hal import (
    OphydTmlMotor, 
    OphydPSUnimag, 
    OphydRTD,
    OphydDI, 
    OphydDO
)

# Initialize devices
motor_x = OphydTmlMotor('SPARC:MOTOR:X', name='x_axis')
magnet = OphydPSUnimag('SPARC:PS:MAG1', name='dipole')
temp_sensor = OphydRTD('SPARC:TEMP:COOL1', name='cooling')
interlock = OphydDI('SPARC:IO:INTERLOCK', name='safety')
beam_enable = OphydDO('SPARC:IO:BEAM_EN', name='beam')

# Check interlock before operation
if interlock.get():
    print("Interlock open - operation allowed")
    
    # Enable beam
    beam_enable.set(1)
    
    # Set magnet current
    magnet.set_current(5.0)
    magnet.set_state(2)  # Turn ON
    
    # Move motor
    motor_x.move(10.0, wait=True)
    
    # Monitor temperature
    temp = temp_sensor.get()
    print(f"Cooling system temperature: {temp}°C")
else:
    print("Interlock closed - operation not allowed")
```

## Integration with Beamline Controller

This library is designed to work seamlessly with the `epik8s-beamline-controller`:

```python
# In your task class
class MyBeamlineTask(TaskBase):
    def initialize(self):
        # Get devices from Ophyd device registry
        self.motor = self.get_device('motor_x')
        self.magnet = self.get_device('dipole_magnet')
        
    def run(self):
        while self.running:
            # Use device methods
            position = self.motor.position()
            current = self.magnet.get_current()
            
            # Your control logic here
            self.step_cycle()
            cothread.Sleep(1.0)
```

## Device Factory Registration

Devices are automatically registered in the controller's device factory:

```yaml
# values.yaml
epicsConfiguration:
  iocs:
    - name: motor_x
      devgroup: motor
      devtype: tml
      iocprefix: SPARC:MOTOR:X
      
    - name: dipole_magnet
      devgroup: magnet
      devtype: unimag
      iocprefix: SPARC:PS:MAG1
```

## Development

### Setting Up Development Environment

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest black flake8
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black infn_ophyd_hal/

# Lint code
flake8 infn_ophyd_hal/
```

## Publishing

### Building Distribution

```bash
pip install wheel twine
python setup.py sdist bdist_wheel
```

### Upload to PyPI

```bash
twine upload dist/*
```

### GitHub Actions

The repository includes automated CI/CD via GitHub Actions:
- Automatic testing on push
- PyPI publishing on tags matching `v*`

Required GitHub secrets:
- `PYPI_USERNAME`
- `PYPI_TOKEN`

## Architecture

### Device Hierarchy

```
Device (Ophyd base)
├── OphydMotor
│   └── OphydTmlMotor
├── OphydPS
│   ├── OphydPSDante
│   ├── OphydPSUnimag
│   └── OphydPSSim
├── OphydBPM
└── I/O Devices
    ├── OphydDI
    ├── OphydDO
    ├── OphydAI
    ├── OphydAO
    └── OphydRTD
```

### Key Concepts

1. **Component (Cpt)**: Ophyd component linking PV suffixes to Python attributes
2. **EpicsSignal**: Read-write EPICS PV
3. **EpicsSignalRO**: Read-only EPICS PV
4. **Device**: Container for related signals

### Extending the Library

To add a new device type:

```python
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO

class OphydMyDevice(Device):
    """My custom device."""
    
    # Define components
    readback = Cpt(EpicsSignalRO, ':RB')
    setpoint = Cpt(EpicsSignal, ':SP')
    
    def get(self):
        """Get current value."""
        return self.readback.get()
    
    def set(self, value):
        """Set value."""
        return self.setpoint.set(value)
```

Then register in `__init__.py`:

```python
from .my_device import OphydMyDevice

__all__ = [
    # ... existing exports
    'OphydMyDevice',
]

# Register in factory
DEVICE_REGISTRY['my_device_type'] = OphydMyDevice
```

## Support and Contributing

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/infn-epics/infn-ophyd-hal/issues)
- **Pull Requests**: Contributions welcome!
- **Documentation**: Additional docs in the `docs/` directory

## License

This project is licensed under the terms specified in the LICENSE file.

## Authors

INFN EPICS Team

## Acknowledgments

Built on the excellent [Ophyd](https://github.com/bluesky/ophyd) framework developed by the Bluesky project at NSLS-II.



