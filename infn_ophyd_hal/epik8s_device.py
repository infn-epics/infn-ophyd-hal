"""
Base class for all EPIK8S Ophyd devices.

This module provides the epik8sDevice base class that all infn_ophyd_hal
device classes should inherit from. It standardizes the initialization
of ophyd Device objects with common arguments.
"""

from ophyd import Device
from typing import Optional, List, Any


class epik8sDevice(Device):
    """
    Base class for all EPIK8S Ophyd devices.
    
    This class standardizes the initialization arguments for all Ophyd
    devices in the infn_ophyd_hal package. It handles common parameters
    like prefix, name, read_attrs, configuration_attrs, and parent.
    
    Parameters
    ----------
    prefix : str
        The EPICS PV prefix for this device
    name : str, optional
        The name of the device instance
    read_attrs : list of str, optional
        Attributes to be read during data acquisition
    configuration_attrs : list of str, optional
        Attributes that define the device configuration
    parent : Device or None, optional
        The parent device instance if this is a sub-device
    **kwargs : dict
        Additional keyword arguments passed to the Device constructor
    """
    def __init__(
        self,
        prefix: str,
        *,
        name: Optional[str] = None,
        read_attrs: Optional[List[str]] = None,
        configuration_attrs: Optional[List[str]] = None,
        parent: Optional[Any] = None,
        **kwargs
    ):
        self._config = kwargs.get('config', None)
        kwargs.pop('config', None)
        """Initialize the EPIK8S device with standard ophyd Device arguments."""
        super().__init__(
            prefix,
            read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            name=name,
            parent=parent,
            **kwargs
        )
    def get_config(self) -> Optional[Any]:
        """Return the device configuration if available."""
        return self._config
    def iocname(self) -> Optional[str]:
        """Return the IOC name from configuration if available."""
        if self._config and isinstance(self._config, dict):
            return self._config.get('iocname', None)
        return None
    def devtype(self) -> Optional[str]:
        """Return the device type from configuration if available."""
        if self._config and isinstance(self._config, dict):
            return self._config.get('devtype', None)
        return None
    def devgroup(self) -> Optional[str]:
        """Return the device group from configuration if available."""
        if self._config and isinstance(self._config, dict):
            return self._config.get('devgroup', None)
        return None
    
