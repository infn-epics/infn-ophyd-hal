#!/usr/bin/env python3
"""
Example script demonstrating the use of DeviceFactory to create
Ophyd devices from a beamline configuration file.
"""

import argparse
import logging
import sys
from pathlib import Path
from infn_ophyd_hal import DeviceFactory, create_devices_from_beamline_config


def setup_logging(level: str = 'INFO'):
    """Configure logging for the example."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_basic_usage(config_path: str):
    """Example 1: Basic usage with convenience function."""
    print("\n" + "="*60)
    print("Example 1: Basic Usage with Convenience Function")
    print("="*60 + "\n")
    
    # Use the convenience function to create all devices
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        print("Please provide a valid beamline configuration file.")
        return
    
    devices = create_devices_from_beamline_config(str(config_file))
    
    print(f"\nCreated {len(devices)} devices:")
    for name, device in devices.items():
        print(f"  - {name}: {type(device).__name__}")


def example_factory_class(config_path: str):
    """Example 2: Using DeviceFactory class directly."""
    print("\n" + "="*60)
    print("Example 2: Using DeviceFactory Class")
    print("="*60 + "\n")
    
    # Create factory instance
    factory = DeviceFactory()
    
    # Show supported device types
    print("Supported device types:")
    supported = factory.get_supported_types()
    for devgroup, devtype in supported:
        print(f"  - {devgroup}/{devtype}")
    
    # Load configuration and create devices
    config_file = Path(config_path)
    
    if config_file.exists():
        config = factory.load_beamline_config(str(config_file))
        devices = factory.create_devices_from_config(config)
        
        print(f"\nCreated {len(devices)} devices from configuration")
    else:
        print(f"\nConfig file not found: {config_file}")


def example_manual_device_creation():
    """Example 3: Creating individual devices manually."""
    print("\n" + "="*60)
    print("Example 3: Manual Device Creation")
    print("="*60 + "\n")
    
    factory = DeviceFactory()
    
    # Create a motor manually
    print("Creating a TML motor device...")
    motor = factory.create_device(
        devgroup='mot',
        devtype='tml',
        prefix='TEST:MOTOR1',
        name='MOTOR1',
        config={'poi': [0, 10, 20, 50, 100]}
    )
    
    if motor:
        print(f"  Created: {motor.name} ({type(motor).__name__})")
        print(f"  Prefix: {motor.prefix}")
    
    # Create a BPM manually
    print("\nCreating a BPM device...")
    bpm = factory.create_device(
        devgroup='diag',
        devtype='bpm',
        prefix='TEST:BPM1',
        name='BPM1',
        config={'devtype': 'libera-spe'}
    )
    
    if bpm:
        print(f"  Created: {bpm.name} ({type(bpm).__name__})")
        print(f"  Prefix: {bpm.prefix}")
    
    # Create a power supply manually
    print("\nCreating a power supply device...")
    ps = factory.create_device(
        devgroup='mag',
        devtype='dante',
        prefix='TEST:PS1',
        name='PS1'
    )
    
    if ps:
        print(f"  Created: {ps.name} ({type(ps).__name__})")
        print(f"  Prefix: {ps.prefix}")


def example_custom_device_registration():
    """Example 4: Registering custom device types."""
    print("\n" + "="*60)
    print("Example 4: Custom Device Registration")
    print("="*60 + "\n")
    
    factory = DeviceFactory()
    
    # In a real scenario, you would import your custom device class
    # from my_devices import MyCustomMotor
    # factory.register_device_type('mot', 'custom', MyCustomMotor)
    
    print("To register a custom device type:")
    print("  factory.register_device_type('mot', 'custom', MyCustomMotor)")
    print("\nThen in your configuration file:")
    print("  devgroup: 'mot'")
    print("  devtype: 'custom'")
    print("\nThe factory will use your custom class for device creation.")


def main():
    """Run all examples."""
    parser = argparse.ArgumentParser(
        description='INFN Ophyd HAL - Device Factory Examples',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s tests/btfmag.yaml
  %(prog)s /path/to/your/beamline_config.yaml
        """
    )
    parser.add_argument(
        'config',
        help='Path to the beamline configuration YAML file'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Validate config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    if not config_path.is_file():
        print(f"Error: {config_path} is not a file")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("INFN Ophyd HAL - Device Factory Examples")
    print(f"Configuration: {config_path}")
    print("="*60)
    
    try:
        example_basic_usage(str(config_path))
        example_factory_class(str(config_path))
        example_manual_device_creation()
        example_custom_device_registration()
        
        print("\n" + "="*60)
        print("Examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
