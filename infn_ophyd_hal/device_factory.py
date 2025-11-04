#!/usr/bin/env python3
"""
Factory for creating Ophyd device instances from beamline configuration.

This module provides a factory class that can read beamline configuration
files (YAML format) and create instances of EPIK8S Ophyd devices based on
the device group and type specified in the configuration.
"""

import logging
import re
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path


class DeviceFactory:
    """Factory for creating EPIK8S Ophyd devices from configuration."""
    
    def __init__(self):
        """Initialize the device factory."""
        self.logger = logging.getLogger(__name__)
        self._device_map = {}
        self._register_device_types()
    
    def _register_device_types(self):
        """Register all available EPIK8S device types."""
        from .tml_ophyd_motor import OphydTmlMotor
        from .spp_ophyd_bpm import SppOphydBpm
        from .ophyd_ps import OphydPS
        from .ophyd_ps_sim import OphydPSSim
        from .ophyd_ps_dantemag import OphydPSDante
        from .unimag_ophyd_ps import OphydPSUnimag
        from .io_basic import OphydDI, OphydDO, OphydAI, OphydAO, OphydRTD
        from .vac_basic import OphydVPC, OphydVGC
        # Register motor devices
        self._device_map[('mot', 'tml')] = OphydTmlMotor
        self._device_map[('mot', 'motor')] = OphydTmlMotor
        
        # Register vacuum devices
        self._device_map[('vac', 'ipcmini')] = OphydVPC
        self._device_map[('vac', 'tpg300')] = OphydVGC
        
        # Register BPM/diagnostic devices
        self._device_map[('diag', 'bpm')] = SppOphydBpm
        self._device_map[('diag', 'libera-spe')] = SppOphydBpm
        self._device_map[('diag', 'libera-sppp')] = SppOphydBpm
        
        # Register power supply devices
        self._device_map[('mag', 'sim')] = OphydPSSim
        self._device_map[('mag', 'dante')] = OphydPSDante
        self._device_map[('mag', 'unimag')] = OphydPSUnimag
        self._device_map[('mag', 'generic')] = OphydPSUnimag
        
        # Register IO devices
        self._device_map[('io', 'rtd')] = OphydRTD
        self._device_map[('io', 'di')] = OphydDI
        self._device_map[('io', 'do')] = OphydDO
        self._device_map[('io', 'ai')] = OphydAI
        self._device_map[('io', 'ao')] = OphydAO
        
        self.logger.info(f"Registered {len(self._device_map)} device types")
    
    def register_device_type(self, devgroup: str, devtype: str, device_class):
        """
        Register a custom device type.
        
        Args:
            devgroup: Device group (e.g., 'mot', 'diag', 'mag', 'io')
            devtype: Device type (e.g., 'tml', 'bpm', 'dante')
            device_class: Ophyd device class to instantiate
        """
        key = (devgroup, devtype)
        self._device_map[key] = device_class
        self.logger.info(f"Registered custom device type: {devgroup}/{devtype}")
    
    def create_device(self, devgroup: str, devtype: str, prefix: str, 
                     name: str, config: Optional[Dict[str, Any]] = None) -> Optional[object]:
        """
        Create an Ophyd device instance.
        
        Args:
            devgroup: Device group (e.g., 'mot', 'diag', 'mag', 'io')
            devtype: Device type (e.g., 'tml', 'bpm', 'dante')
            prefix: EPICS PV prefix
            name: Device name
            config: Additional configuration dictionary
            
        Returns:
            Ophyd device instance or None if type not supported
        """
        # Try device-specific devtype override first
        device_specific_type = config.get('devtype') if config and isinstance(config, dict) else None
        
        device_class = None
        if device_specific_type:
            device_class = self._device_map.get((devgroup, device_specific_type))
        
        # Try exact devtype match if override not found
        if not device_class:
            key = (devgroup, devtype)
            device_class = self._device_map.get(key)
        
        # Try with generic type if specific not found
        if not device_class:
            key = (devgroup, 'generic')
            device_class = self._device_map.get(key)
        
        if not device_class:
            self.logger.warning(
                f"No device class registered for {devgroup}/{devtype}, "
                f"device {name} will not be created"
            )
            return None
        
        try:
            # Prepare kwargs for device creation
            kwargs = {
                'prefix': prefix,
                'name': name
            }
            
            # Add config if provided
            if config:
                kwargs['config'] = config
                
                # Add POI (Points of Interest) for motors if available
                if 'poi' in config or 'iocinit' in config:
                    kwargs['poi'] = config.get('poi', config.get('iocinit', []))
            
            # Create device instance
            device = device_class(**kwargs)
            
            self.logger.debug(f"Created {device_class.__name__} for {name} with prefix {prefix}")
            return device
            
        except Exception as e:
            self.logger.error(
                f"Failed to create device {name} ({devgroup}/{devtype}): {e}",
                exc_info=True
            )
            return None
    
    def get_supported_types(self) -> List[tuple]:
        """
        Get list of supported (devgroup, devtype) combinations.
        
        Returns:
            List of tuples (devgroup, devtype)
        """
        return list(self._device_map.keys())
    
    def _matches_filters(self, device_name: str, device_config: Dict[str, Any],
                        name_pattern: Optional[str] = None,
                        devtype: Optional[str] = None,
                        devgroup: Optional[str] = None,
                        **custom_filters) -> bool:
        """
        Check if a device matches the specified filters.
        
        Args:
            device_name: Name of the device
            device_config: Device configuration dictionary
            name_pattern: Regex pattern to match device name (optional)
            devtype: Device type to match (optional, exact match or regex)
            devgroup: Device group to match (optional, exact match or regex)
            **custom_filters: Additional key-value filters (e.g., zone='beam1')
                             Supports regex patterns if value starts with 'regex:'
        
        Returns:
            True if device matches all specified filters, False otherwise
        """
        # Check name pattern
        if name_pattern:
            try:
                if not re.search(name_pattern, device_name, re.IGNORECASE):
                    return False
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{name_pattern}': {e}")
                return False
        
        # Check devtype
        if devtype:
            device_devtype = device_config.get('devtype', '')
            try:
                # Try as regex first
                if not re.search(devtype, device_devtype, re.IGNORECASE):
                    # Also try exact match (case-insensitive)
                    if device_devtype.lower() != devtype.lower():
                        return False
            except re.error:
                # If regex fails, do exact match
                if device_devtype.lower() != devtype.lower():
                    return False
        
        # Check devgroup
        if devgroup:
            device_devgroup = device_config.get('devgroup', '')
            try:
                # Try as regex first
                if not re.search(devgroup, device_devgroup, re.IGNORECASE):
                    # Also try exact match (case-insensitive)
                    if device_devgroup.lower() != devgroup.lower():
                        return False
            except re.error:
                # If regex fails, do exact match
                if device_devgroup.lower() != devgroup.lower():
                    return False
        
        # Check custom filters (e.g., zone, location, etc.)
        for key, value in custom_filters.items():
            if value is None:
                continue
            
            config_value = device_config.get(key, '')
            if not config_value:
                return False
            # Convert to string for comparison
            if not isinstance(config_value, str):
                config_value = str(config_value)
            
            # Check if value is a regex pattern (prefixed with 'regex:')
            if isinstance(value, str) and value.startswith('regex:'):
                pattern = value[6:]  # Remove 'regex:' prefix
                try:
                    if not re.search(pattern, config_value, re.IGNORECASE):
                        return False
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern '{pattern}' for key '{key}': {e}")
                    return False
            else:
                # Try regex match first
                try:
                    if isinstance(value, list):
                        matched = False
                        for v in value:
                            if re.search(str(v), config_value, re.IGNORECASE):
                                matched = True
                                break
                        if not matched:
                            return False
                    if not re.search(str(value), config_value, re.IGNORECASE):
                        # Also try exact match (case-insensitive)
                        if config_value.lower() != str(value).lower():
                            return False
                except re.error:
                    # If regex fails, do exact match
                    if config_value.lower() != str(value).lower():
                        return False
        
        return True
    
    def load_beamline_config(self, config_path: str) -> Dict:
        """
        Load beamline configuration from YAML file.
        
        Args:
            config_path: Path to beamline YAML configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Loaded beamline configuration from {config_path}")
                return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def create_devices_from_config(self, config: Dict,
                                   name_pattern: Optional[str] = None,
                                   devtype: Optional[str] = None,
                                   devgroup: Optional[str] = None,
                                   **custom_filters) -> Dict[str, object]:
        """
        Create Ophyd devices from beamline configuration with optional filtering.
        
        Args:
            config: Beamline configuration dictionary (typically from values.yaml)
            name_pattern: Regex pattern to filter devices by name (optional)
            devtype: Filter by device type (exact match or regex) (optional)
            devgroup: Filter by device group (exact match or regex) (optional)
            **custom_filters: Additional filters (e.g., zone='beam1', location='hall')
                             Prefix value with 'regex:' for regex matching
        
        Returns:
            Dictionary mapping device names to Ophyd device instances
            
        Examples:
            # Create only motors
            factory.create_devices_from_config(config, devgroup='mot')
            
            # Create devices with names starting with 'BPM'
            factory.create_devices_from_config(config, name_pattern=r'^BPM')
            
            # Create magnets in zone 'beam1'
            factory.create_devices_from_config(config, devgroup='mag', zone='beam1')
            
            # Create devices with names containing digits
            factory.create_devices_from_config(config, name_pattern=r'\d+')
        """
        devices = {}
        
        # Get IOC configurations
        epics_config = config.get('epicsConfiguration', {})
        iocs = epics_config.get('iocs', [])
        
        if not iocs:
            self.logger.warning("No IOCs found in configuration")
            return devices
        
        # Log filter information
        if name_pattern or devtype or devgroup or custom_filters:
            filter_info = []
            if name_pattern:
                filter_info.append(f"name_pattern='{name_pattern}'")
            if devtype:
                filter_info.append(f"devtype='{devtype}'")
            if devgroup:
                filter_info.append(f"devgroup='{devgroup}'")
            for key, value in custom_filters.items():
                filter_info.append(f"{key}='{value}'")
            self.logger.info(f"Applying filters: {', '.join(filter_info)}")
        
        self.logger.info(f"Processing {len(iocs)} IOC configurations...")
        
        for ioc_config in iocs:
            ioc_name = ioc_config.get('name')
            if not ioc_name:
                continue
            
            # Check if IOC is disabled
            if ioc_config.get('disable', False):
                self.logger.debug(f"Skipping disabled IOC: {ioc_name}")
                continue
            
            # Get device group and type from IOC config
            ioc_devgroup = ioc_config.get('devgroup')
            ioc_devtype = ioc_config.get('devtype')
            
            if not ioc_devgroup:
                self.logger.debug(f"IOC {ioc_name} has no devgroup, skipping")
                continue
            
            # Get IOC prefix for PV construction
            ioc_prefix = ioc_config.get('iocprefix', '')
            
            # Get devices list (for IOCs with multiple devices)
            device_list = ioc_config.get('devices', [])
            
            try:
                if device_list:
                    # Create Ophyd instance for each device
                    for device_config in device_list:
                        device_name = device_config.get('name')
                        if not device_name:
                            continue
                        
                        # Merge IOC config with device config for filter checking
                        merged_config = ioc_config.copy()
                        merged_config['iocname'] = ioc_name
                        merged_config.update(device_config)
                        
                        # Apply filters
                        if not self._matches_filters(device_name, merged_config,
                                                     name_pattern, devtype, devgroup,
                                                     **custom_filters):
                            self.logger.debug(f"Device {device_name} filtered out")
                            continue
                        
                        # Construct PV prefix
                        if 'iocroot' in ioc_config:
                            pv_prefix = f"{ioc_prefix}:{ioc_config['iocroot']}:{device_name}"
                        else:
                            pv_prefix = f"{ioc_prefix}:{device_name}"
                        
                        # Create Ophyd device
                        ophyd_device = self.create_device(
                            devgroup=ioc_devgroup,
                            devtype=ioc_devtype,
                            prefix=pv_prefix,
                            name=device_name,
                            config=merged_config
                        )
                        
                        if ophyd_device:
                            device_key = device_name
                            
                            # Handle name conflicts
                            if device_key in devices:
                                device_key = f"{ioc_name}_{device_name}"
                                self.logger.warning(
                                    f"Device name '{device_name}' already exists, "
                                    f"renaming to '{device_key}'"
                                )
                                
                                if device_key in devices:
                                    self.logger.error(
                                        f"Renamed device key '{device_key}' also exists. "
                                        f"Skipping device creation for {device_name} in IOC {ioc_name}."
                                    )
                                    continue
                            
                            devices[device_key] = ophyd_device
                            self.logger.info(
                                f"Created device: {device_key} "
                                f"({ioc_name}/{ioc_devgroup}/{ioc_devtype} prefix={pv_prefix})"
                            )
                else:
                    # Single device IOC
                    # Apply filters
                    if not self._matches_filters(ioc_name, ioc_config,
                                                 name_pattern, devtype, devgroup,
                                                 **custom_filters):
                        self.logger.debug(f"Device {ioc_name} filtered out")
                        continue
                    
                    pv_prefix = ioc_prefix
                    
                    # Create Ophyd device
                    ophyd_device = self.create_device(
                        devgroup=ioc_devgroup,
                        devtype=ioc_devtype,
                        prefix=pv_prefix,
                        name=ioc_name,
                        config=ioc_config
                    )
                    
                    if ophyd_device:
                        devices[ioc_name] = ophyd_device
                        self.logger.info(
                                f"Created device: {ioc_name} "
                                f"({ioc_name}/{ioc_devgroup}/{ioc_devtype} prefix={pv_prefix})"
                        )
                       
                        
            except Exception as e:
                self.logger.error(
                    f"Failed to create devices for IOC {ioc_name}: {e}",
                    exc_info=True
                )
        
        self.logger.info(f"Created {len(devices)} Ophyd devices from configuration")
        return devices
    
    def create_devices_from_file(self, config_path: str,
                                 name_pattern: Optional[str] = None,
                                 devtype: Optional[str] = None,
                                 devgroup: Optional[str] = None,
                                 **custom_filters) -> Dict[str, object]:
        """
        Create Ophyd devices from beamline configuration file with optional filtering.
        
        Args:
            config_path: Path to beamline YAML configuration file
            name_pattern: Regex pattern to filter devices by name (optional)
            devtype: Filter by device type (exact match or regex) (optional)
            devgroup: Filter by device group (exact match or regex) (optional)
            **custom_filters: Additional filters (e.g., zone='beam1', location='hall')
            
        Returns:
            Dictionary mapping device names to Ophyd device instances
        """
        config = self.load_beamline_config(config_path)
        return self.create_devices_from_config(config, name_pattern, devtype, 
                                              devgroup, **custom_filters)


def create_devices_from_beamline_config(config_path: str,
                                        name_pattern: Optional[str] = None,
                                        devtype: Optional[str] = None,
                                        devgroup: Optional[str] = None,
                                        **custom_filters) -> Dict[str, object]:
    """
    Convenience function to create devices from a beamline configuration file.
    
    Args:
        config_path: Path to beamline YAML configuration file
        name_pattern: Regex pattern to filter devices by name (optional)
        devtype: Filter by device type (exact match or regex) (optional)
        devgroup: Filter by device group (exact match or regex) (optional)
        **custom_filters: Additional filters (e.g., zone='beam1')
        
    Returns:
        Dictionary mapping device names to Ophyd device instances
    
    Examples:
        >>> # Create all devices
        >>> devices = create_devices_from_beamline_config('values.yaml')
        >>> motor1 = devices['MOTOR1']
        >>> motor1.user_readback.get()
        
        >>> # Create only motors
        >>> motors = create_devices_from_beamline_config('values.yaml', devgroup='mot')
        
        >>> # Create devices with names matching pattern
        >>> bpms = create_devices_from_beamline_config('values.yaml', name_pattern=r'^BPM')
        
        >>> # Create magnets in specific zone
        >>> magnets = create_devices_from_beamline_config('values.yaml', 
        ...                                               devgroup='mag', 
        ...                                               zone='beam1')
    """
    factory = DeviceFactory()
    return factory.create_devices_from_file(config_path, name_pattern, devtype,
                                           devgroup, **custom_filters)
