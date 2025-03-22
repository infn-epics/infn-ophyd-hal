from infn_ophyd_hal import PowerSupplyFactory,ophyd_ps_state
import time
import yaml
import argparse
verbose=1
def load_config(filename):
    with open(filename, "r") as f:
        return yaml.safe_load(f)

def current_change_callback(new_value,psa):
        if verbose>1:
            print(f"[{psa.name}] Current updated to: {new_value:.2f} A")

def state_change_callback(new_state,psa):
    if verbose:
        print(f"{psa.name} State updated to: {new_state}")
   
def wait_state(ps,state,tim):
    now=time.time()
    
    while True:
        diff=time.time() - now
        if diff> tim:
            print(f"{ps.name} state {state} not reached in {tim} seconds")
            return -1
        
        if ps.get_state()==state:
            return 0
        time.sleep(1)
        
        
         
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
            params['verbose']=1
            ps = PowerSupplyFactory.create(driver,name,prefix=f"{p}:{root}",**params)
            ps.on_current_change = current_change_callback
            ps.on_state_change = state_change_callback
            psa.append(ps)
    print("* Wating 10 s")
    time.sleep(10) # see what happens at the beginning
    errs=0
    ok=0
    for p in psa:
        print(f"* {p.name} in {p.get_state()}")
              
    for p in psa:
        if p.get_state()!= "STANDBY":
            print(f"* {p.name} setting in  STDBY")
            p.set_state("STANDBY")
            if p.wait(60)!=0:
                errs=errs+1
            

    if errs > 0:
        print("## failed state test")
        return -1

    

    
    for p in psa:
        p.set_state("ON")
        if p.wait(60)!=0:
                return
        feat=p.get_features()
        l=[int(feat['min']),int(feat['max'])]
        l.extend(range(int(feat['min']),int(feat['max'])))
        for curr in l:
            print(f"* {p.name} setting current {curr}, waiting {feat['slope']*10} to read back.")
            p.set_current(curr)
            p.wait(60)
            rd=p.get_current()
            if abs(rd-curr)>feat['curr_th']:
                print(f"# {p.name} didnt reached setpoint {curr} - readout {rd} = {abs(curr-rd)} > {feat['curr_th']} ")
                errs = errs+1
            else:
                print(f"* {p.name} reached setpoint {curr} - readout {rd} = {abs(curr-rd)} < {feat['curr_th']}")
                ok = ok +1

    
    
    time.sleep(10)
    cnt=0
    for p in psa:
        print(f"* {ps.name} reached  current:{p.get_current()} setting STBY")
        p.set_state("STANDBY")
        p.wait(60)


    print(f"* Result {ok}/{ok+errs} OK")



if __name__ == "__main__":
    main()