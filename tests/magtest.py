from infn_ophyd_hal import PowerSupplyFactory,ophyd_ps_state
import time
import yaml
import argparse

def load_config(filename):
    with open(filename, "r") as f:
        return yaml.safe_load(f)

def current_change_callback(new_value,psa):
        print(f"[{psa.name} Current updated to: {new_value:.2f} A")

def state_change_callback(new_state,psa):
        print(f"{psa.name} State updated to: {new_state}")
        
def main():
    
    parser = argparse.ArgumentParser(description="EPICS Soft IOC for unified power supplies interface ")
    parser.add_argument(
        "config", type=str, help="Path to the configuration YAML file."
        
    )
    args = parser.parse_args()

    # Load YAML Configuration
    config = load_config(args.config)
    
    for magnet in config["magnets"]:
        for name, details in magnet.items():
            driver = details["driver"]
            p = details["prefix"]
            root = details["root"]
            params = details.get("param", {})
            ps = PowerSupplyFactory.create(driver,name,prefix=f"{p}:{root}",**params)
            ps.on_current_change = current_change_callback
            ps.on_state_change = state_change_callback
    
    try:
            time.sleep(20)
    finally:
        print(f"* {ps.name} reached  current:{ps.get_current()}")



if __name__ == "__main__":
    main()