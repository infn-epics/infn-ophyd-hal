import argparse
import logging
from infn_ophyd_hal.device_factory import DeviceFactory, create_devices_from_beamline_config


def myreadupdate(timestamp=None, value=None, **kwargs):
    print(f" read {value}")


def main():
    """Entry point for the bpm test script.

    Accepts application parameters for configuration file and log level/debug flag.
    """
    parser = argparse.ArgumentParser(description="BPM test runner")
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
    devices = factory.create_devices_from_file(args.config, devtype='bpm')
    print(f"Created {len(devices)} BPM devices: {list(devices.keys())}")
    for i in devices.values():
        i.x.subscribe(myreadupdate)
        i.reset()  # reset counter
        i.thsld(100)
        print(f"{i.name} cnt:{i.cnt.get()} thshld:{i.ths.get()} X:{i.x.get()} Y:{i.y.get()} VA:{i.va.get()} VB:{i.vb.get()} VC:{i.vc.get()} VD:{i.vd.get()} SUM:{i.sum.get()}")

if __name__ == "__main__":
    main()

# for i in ["AC1BPM01","AC2BPM01","AC3BPM01","PTLBPM01"]:
#     bpm = SppOphydBpm(i,name=i)
#     bpm.reset()## reset counter
#     bpm.thsld(100)

#     print(f"{i} cnt:{bpm.cnt.get()} thshld:{bpm.ths.get()} X:{bpm.x.get()} Y:{bpm.y.get()} VA:{bpm.va.get()} VB:{bpm.vb.get()} VC:{bpm.vc.get()} VD:{bpm.vd.get()} SUM:{bpm.sum.get()}")

    
# Perform motor actions
# motor.home()
# motor.set(100)