#!/usr/bin/env python3
"""
Motor test script.

This script creates motor devices from a beamline configuration and tests
basic motor operations like reading position, moving, homing, and checking status.
"""

import argparse
import logging
from infn_ophyd_hal.device_factory import DeviceFactory, create_devices_from_beamline_config


def on_position_change(timestamp=None, value=None, **kwargs):
    """Callback for position changes."""
    print(f"Position changed: {value}")


def main():
    """Entry point for the motor test script.

    Accepts application parameters for configuration file and log level/debug flag.
    """
    parser = argparse.ArgumentParser(description="Motor test runner")
    parser.add_argument("--config", "-c", default="sparc_beamline.yaml",
                        help="Path to beamline YAML configuration file (default: sparc_beamline.yaml)")

    level_group = parser.add_mutually_exclusive_group()
    level_group.add_argument("--log-level", "-l", default="INFO",
                             choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                             help="Logging level (default: INFO)")
    level_group.add_argument("--debug", action="store_true",
                             help="Shortcut to set log level to DEBUG")

    args = parser.parse_args()

    # Configure logging
    chosen_level = "DEBUG" if args.debug else args.log_level
    logging.basicConfig(level=getattr(logging, chosen_level.upper(), logging.INFO),
                        format="%(name)s - %(levelname)s - %(message)s")

    # Create devices using provided configuration
    factory = DeviceFactory()
    devices = factory.create_devices_from_file(args.config, devgroup='mot')
    print(f"Created {len(devices)} motor devices: {list(devices.keys())}")

    for name, device in devices.items():
        print(f"\n=== Testing {name} ({device.__class__.__name__}) ===")

        try:
            # Get current position and status
            position = device.position()
            is_moving = device.moving()
            is_homed = device.ishomed()
            has_error = device.iserror()
            limit_status = device.limit()

            print(f"{name} position: {position}, moving: {is_moving}, homed: {is_homed}, error: {has_error}, limit: {limit_status}")

            # Subscribe to position changes (for demonstration)
            device.user_readback.subscribe(on_position_change)

            # Decode full status
            status_info = device.decode()
            print(f"{name} status:\n{status_info}")

        
        except Exception as e:
            print(f"Error testing {name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

# Example usage with different filters:
# python mottest.py --config sparc_beamline.yaml --log-level DEBUG
# python mottest.py --config sparc_beamline.yaml --log-level INFO
#
# Or programmatically:
# from infn_ophyd_hal.device_factory import create_devices_from_beamline_config
# motors = create_devices_from_beamline_config('sparc_beamline.yaml', devgroup='mot')
# for name, motor in motors.items():
#     print(f"{name}: position={motor.position()}, moving={motor.moving()}")
