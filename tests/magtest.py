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
    psa=[]
    
    for magnet in config["magnets"]:
        for name, details in magnet.items():
            driver = details["driver"]
            p = details["prefix"]
            root = details["root"]
            params = details.get("param", {})
            ps = PowerSupplyFactory.create(driver,name,prefix=f"{p}:{root}",**params)
            ps.on_current_change = current_change_callback
            ps.on_state_change = state_change_callback
            ps.set_state("ON")
            ps.set_current(2)
            ps.set_current(-2)
            psa.append(ps)
    
    
        time.sleep(20)
        cnt=0
        for p in psa:
            print(f"* {ps.name} reached  current:{p.get_current()}")
            p.set_state("STANDBY")
        while cnt<2:
            for p in psa:
                if p.get_state() == "STANDBY":
                    print(f"* {ps.name} reached  current:{p.get_current()} state {p.get_state()}")
                    cnt=cnt+1
            time.sleep(1)


        



if __name__ == "__main__":
    main()