# epik8sDevice Base Class

## Overview

All device classes in `infn_ophyd_hal` now inherit from a common base class `epik8sDevice`, which itself inherits from `ophyd.Device`. This standardizes the initialization of all Ophyd devices in the package.

## Architecture

```
ophyd.Device
    ↓
epik8sDevice (new base class)
    ↓
    ├── OphydTmlMotor (also inherits from PositionerBase)
    ├── SppOphydBpm
    ├── OphydDI
    ├── OphydDO
    ├── OphydAI
    ├── OphydAO
    ├── OphydRTD
    ├── OphydPSDante (also inherits from OphydPS)
    └── OphydPSUnimag (also inherits from OphydPS)
```

## Benefits

1. **Standardized Initialization**: All devices now use consistent parameter names and initialization patterns
2. **Centralized Configuration**: Common device configuration is handled in one place
3. **Easier Maintenance**: Changes to base device behavior can be made in one location
4. **Type Safety**: Better type hints and IDE support for device parameters
5. **Future Extensibility**: Easy to add common functionality to all devices

## Base Class Parameters

The `epik8sDevice` base class accepts the following standard ophyd Device parameters:

- `prefix` (str): The EPICS PV prefix for this device
- `name` (str, optional): The name of the device instance
- `read_attrs` (list of str, optional): Attributes to be read during data acquisition
- `configuration_attrs` (list of str, optional): Attributes that define the device configuration
- `parent` (Device or None, optional): The parent device instance if this is a sub-device
- `**kwargs`: Additional keyword arguments passed to the Device constructor

## Files Modified

1. **New File**: `infn_ophyd_hal/epik8s_device.py` - Base class definition
2. **Modified**: `infn_ophyd_hal/__init__.py` - Exports epik8sDevice
3. **Modified**: `infn_ophyd_hal/tml_ophyd_motor.py` - OphydTmlMotor now inherits from epik8sDevice
4. **Modified**: `infn_ophyd_hal/spp_ophyd_bpm.py` - SppOphydBpm now inherits from epik8sDevice
5. **Modified**: `infn_ophyd_hal/io_basic.py` - All IO classes now inherit from epik8sDevice
6. **Modified**: `infn_ophyd_hal/ophyd_ps_dantemag.py` - OphydPSDante now inherits from epik8sDevice
7. **Modified**: `infn_ophyd_hal/unimag_ophyd_ps.py` - OphydPSUnimag now inherits from epik8sDevice

## Usage

No changes are required for existing code that uses these device classes. The API remains the same:

```python
from infn_ophyd_hal import OphydTmlMotor, SppOphydBpm, epik8sDevice

# Create devices as before
motor = OphydTmlMotor(prefix="MOTOR:01", name="my_motor")
bpm = SppOphydBpm(prefix="BPM:01", name="my_bpm")

# The base class can also be imported if needed for type checking or custom devices
if isinstance(motor, epik8sDevice):
    print("Motor is an epik8sDevice!")
```

## Backward Compatibility

All existing functionality is preserved. The change is purely structural and does not affect the public API of any device class.
