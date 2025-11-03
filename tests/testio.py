#!/usr/bin/env python3
"""
Test script for IO devices (Digital Input/Output, Analog Input/Output, RTD)

Usage:
    python testio.py [device_type] [pv_prefix]

Examples:
    python testio.py do TEST:IO:DO1    # Test digital output
    python testio.py di TEST:IO:DI1    # Test digital input
    python testio.py ao TEST:IO:AO1    # Test analog output
    python testio.py ai TEST:IO:AI1    # Test analog input
    python testio.py rtd TEST:TEMP:RTD1  # Test RTD temperature
    python testio.py all               # Test all devices (default)
"""

import logging
import time
import argparse
from infn_ophyd_hal import OphydDO, OphydDI, OphydAO, OphydAI, OphydRTD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_digital_output(pv_prefix="TEST:IO:DO1"):
    """Test digital output device."""
    print(f"\n--- Testing Digital Output ({pv_prefix}) ---")
    
    try:
        # Create device
        do_device = OphydDO(pv_prefix, name='test_do')
        
        # Test initial state
        initial_value = do_device.get()
        print(f"Initial value: {initial_value}")
        
        # Test setting to 1
        print("Setting to 1...")
        do_device.set(1)
        time.sleep(5.0)  # Allow time for EPICS to process
        
        value_after_1 = do_device.get()
        print(f"Value after setting to 1: {value_after_1}")
        assert value_after_1 == 1, f"Expected 1, got {value_after_1}"
        
        # Test setting to 0
        print("Setting to 0...")
        do_device.set(0)
        time.sleep(0.1)
        
        value_after_0 = do_device.get()
        print(f"Value after setting to 0: {value_after_0}")
        assert value_after_0 == 0, f"Expected 0, got {value_after_0}"
        
        print("✓ Digital output test passed")
        return True
        
    except Exception as e:
        print(f"✗ Digital output test failed: {e}")
        return False

def test_digital_input(pv_prefix="TEST:IO:DI1"):
    """Test digital input device."""
    print(f"\n--- Testing Digital Input ({pv_prefix}) ---")
    
    try:
        # Create device
        di_device = OphydDI(pv_prefix, name='test_di')
        
        # Test reading value
        value = di_device.get()
        print(f"Current value: {value}")
        
        # Verify it's a valid digital value (0 or 1)
        assert value in [0, 1], f"Expected 0 or 1, got {value}"
        
        print("✓ Digital input test passed")
        return True
        
    except Exception as e:
        print(f"✗ Digital input test failed: {e}")
        return False

def test_analog_output(pv_prefix="TEST:IO:AO1"):
    """Test analog output device."""
    print(f"\n--- Testing Analog Output ({pv_prefix}) ---")
    
    try:
        # Create device
        ao_device = OphydAO(pv_prefix, name='test_ao')
        
        # Test initial state
        initial_value = ao_device.get()
        print(f"Initial value: {initial_value}")
        
        # Test setting to different values
        test_values = [0.0, 2.5, 5.0, 7.5, 10.0]
        
        for test_val in test_values:
            print(f"Setting to {test_val}...")
            ao_device.set(test_val)
            time.sleep(0.1)
            
            read_value = ao_device.get()
            print(f"Read back: {read_value}")
            
            # Allow small tolerance for floating point
            tolerance = 0.01
            assert abs(read_value - test_val) < tolerance, f"Expected ~{test_val}, got {read_value}"
        
        print("✓ Analog output test passed")
        return True
        
    except Exception as e:
        print(f"✗ Analog output test failed: {e}")
        return False

def test_analog_input(pv_prefix="TEST:IO:AI1"):
    """Test analog input device."""
    print(f"\n--- Testing Analog Input ({pv_prefix}) ---")
    
    try:
        # Create device
        ai_device = OphydAI(pv_prefix, name='test_ai')
        
        # Test reading value
        value = ai_device.get()
        print(f"Current value: {value}")
        
        # Verify it's a reasonable analog value (between -10 and 10V for example)
        assert -20.0 <= value <= 20.0, f"Value {value} seems unreasonable for analog input"
        
        print("✓ Analog input test passed")
        return True
        
    except Exception as e:
        print(f"✗ Analog input test failed: {e}")
        return False

def test_rtd(pv_prefix="TEST:TEMP:RTD1"):
    """Test RTD temperature device."""
    print(f"\n--- Testing RTD Temperature ({pv_prefix}) ---")
    
    try:
        # Create device
        rtd_device = OphydRTD(pv_prefix, name='test_rtd')
        
        # Test reading temperature
        temperature = rtd_device.get()
        print(f"Current temperature: {temperature} °C")
        
        # Verify it's a reasonable temperature value (between -50 and 200°C for example)
        assert -50.0 <= temperature <= 200.0, f"Temperature {temperature}°C seems unreasonable"
        
        print("✓ RTD temperature test passed")
        return True
        
    except Exception as e:
        print(f"✗ RTD temperature test failed: {e}")
        return False

def main():
    """Run IO device tests based on command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test IO devices from infn-ophyd-hal library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python testio.py do TEST:IO:DO1     # Test digital output
  python testio.py di TEST:IO:DI1     # Test digital input
  python testio.py ao TEST:IO:AO1     # Test analog output
  python testio.py ai TEST:IO:AI1     # Test analog input
  python testio.py rtd TEST:TEMP:RTD1 # Test RTD temperature
  python testio.py all                # Test all devices (default)
        """
    )
    
    parser.add_argument(
        'device_type',
        nargs='?',
        default='all',
        choices=['do', 'di', 'ao', 'ai', 'rtd', 'all'],
        help='Type of IO device to test (default: all)'
    )
    
    parser.add_argument(
        'pv_prefix',
        nargs='?',
        help='EPICS PV prefix for the device (optional, uses defaults if not specified)'
    )
    
    args = parser.parse_args()
    
    print("INFN Ophyd HAL - IO Device Tests")
    print("=================================")
    
    # Map device types to test functions and default PVs
    device_map = {
        'do': ('Digital Output', test_digital_output, 'TEST:IO:DO1'),
        'di': ('Digital Input', test_digital_input, 'TEST:IO:DI1'),
        'ao': ('Analog Output', test_analog_output, 'TEST:IO:AO1'),
        'ai': ('Analog Input', test_analog_input, 'TEST:IO:AI1'),
        'rtd': ('RTD Temperature', test_rtd, 'TEST:TEMP:RTD1')
    }
    
    if args.device_type == 'all':
        # Run all tests
        results = []
        
        for device_type, (name, test_func, default_pv) in device_map.items():
            pv_to_use = args.pv_prefix if args.pv_prefix else default_pv
            success = test_func(pv_to_use)
            results.append((name, success))
        
        # Summary
        print("\n=== Test Summary ===")
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            status = "PASS" if success else "FAIL"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed. Check EPICS IOC setup.")
            return 1
    
    else:
        # Run specific test
        name, test_func, default_pv = device_map[args.device_type]
        pv_to_use = args.pv_prefix if args.pv_prefix else default_pv
        
        print(f"Testing {name} with PV: {pv_to_use}")
        
        success = test_func(pv_to_use)
        
        if success:
            print(f"\n✓ {name} test passed!")
            return 0
        else:
            print(f"\n✗ {name} test failed!")
            return 1

if __name__ == "__main__":
    exit(main())
