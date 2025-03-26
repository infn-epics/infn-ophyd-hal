from infn_ophyd_hal import PowerSupplyFactory, ophyd_ps_state
import time
import csv
import yaml
import argparse
from datetime import datetime
import re  # Import the regular expression module

verbose = 1

def log(message):
    """Helper function to print messages with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_csvconfig(filename):
    selection = {}
    selection['magnets'] = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            param={}

            # Extract relevant fields
            if row["Type"] == "COR":
                param['bipolar'] = True
            
            if 'Bipolar' in row:
                if row['Bipolar']== '1':
                    param['bipolar'] = True
                if row['Bipolar']== '0':
                    param['bipolar'] = False   

                
            if 'Max' in row and not isinstance(row['Max'], str) and row['Max'].replace('.', '', 1).isdigit():
                param['max'] = float(row['Max'])  # Convert to a float
            else:
                param['max'] = 2  # Default value

            if 'Min' in row and not isinstance(row['Min'], str) and row['Min'].replace('.', '', 1).isdigit():
                param['min'] = float(row['Min'])  # Convert to a float
            else:
                param['min'] = -2  # Default value
                
            desc=""
            if 'Description' in row:
                desc=row['Description']
            selection['magnets'].append({row["Name"]:{
                "prefix": row["Prefix"],
                "root": row["Name"],
                "zone": row["Zone"],
                "type": row["Type"],
                "param": param,
                "driver": row["Driver"],
                "desc": desc
            }})
    return selection
def load_config(filename):
    with open(filename, "r") as f:
        return yaml.safe_load(f)

def current_change_callback(new_value, psa):
    if verbose > 1:
        log(f"[{psa.name}] Current updated to: {new_value:.2f} A")

def state_change_callback(new_state, psa):
    if verbose:
        log(f"{psa.name} State updated to: {new_state}")

def wait_state(ps, state, tim):
    now = time.time()

    while True:
        diff = time.time() - now
        if diff > tim:
            log(f"{ps.name} state {state} not reached in {tim} seconds")
            return -1

        if ps.get_state() == state:
            return 0
        time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="EPICS Soft IOC for unified power supplies interface ")
    parser.add_argument(
        "config", type=str, help="Path to the configuration YAML or CSV file."
    )
    parser.add_argument(
        "--type", type=str, default="ALL", help="Type to test (e.g., QUA, COR, DIP)"
    )
    parser.add_argument(
        "--zone", type=str, default="ALL", help="Zone to test (e.g., TM, TB)"
    )
    parser.add_argument(
        "--regexp", type=str, default=".*", help="Regular expression to filter magnet names"
    )
    parser.add_argument(
        "--verbose", type=int, default=1, help="Regular expression to filter magnet names"
    )
    args = parser.parse_args()
    verbose = args.verbose

    # Load configuration based on file type
    if args.config.endswith(".csv"):
        config = load_csvconfig(args.config)
    elif args.config.endswith(".yaml"):
        config = load_config(args.config)
    else:
        print(f"Error: unsupported file type {args.config}. Supported types: .yaml | .csv")
        return  

    # Compile the regular expression for filtering names
    name_pattern = re.compile(args.regexp)

    # Filter magnets based on type, zone, and name
    filtered_magnets = []
    for magnet in config["magnets"]:
        for name, details in magnet.items():
            # Apply filters
            if (args.type == "ALL" or details["type"] == args.type) and \
               (args.zone == "ALL" or details["zone"] == args.zone) and \
               name_pattern.match(name):
                filtered_magnets.append(magnet)

    if not filtered_magnets:
        print("No magnets match the specified filters.")
        return

    psa = []

    # Create power supplies for the filtered magnets
    for magnet in filtered_magnets:
        for name, details in magnet.items():
            driver = details["driver"]
            p = details["prefix"]
            root = details["root"]
            params = details.get("param", {})
            params['verbose'] = verbose
            try:
                ps = PowerSupplyFactory.create(driver, name, prefix=f"{p}:{root}", **params)
                ps.on_current_change = current_change_callback
                ps.on_state_change = state_change_callback
                psa.append(ps)
            except Exception as e:
                log(f"## Failed to create power supply for {name}: {e}")
    if len(psa) == 0:
        log("## No power supplies created")
        return -1
        
    log("* Waiting 10 s")
    time.sleep(10)  # See what happens at the beginning
    errs = 0
    ok = 0
    for p in psa:
        log(f"* {p.name} in {p.get_state()}")

    for p in psa:
        st = p.get_state()
        if st != "STANDBY":
            log(f"********************** {p.name} setting in STDBY")
            p.set_state("STANDBY")
            if p.wait(60) != 0:
                st = p.get_state()
                errs = errs + 1
                log(f"# {p.name} failed setting in STANDBY is in '{st}'")

    if errs > 0:
        log("## failed state test")
        return -1

    for p in psa:
        log(f"***** {p.name} setting in ON *****")

        p.set_state("ON")
        if p.wait(60) != 0:
            log(f"# {p.name} failed setting in ON")
            errs = errs + 1
            continue

        feat = p.get_features()
        l = [int(feat['min']), int(feat['max'])]
        l.extend(range(int(feat['min']), int(feat['max'])))
        for curr in l:
            log(f"**** {p.name} setting current {curr}, waiting {feat['slope']*10} to read back. ***")
            p.set_current(curr)
            p.wait(60)
            rd = p.get_current()
            if abs(rd - curr) > feat['curr_th']:
                log(f"# {p.name} didn't reach setpoint {curr} - readout {rd} = {abs(curr-rd)} > {feat['curr_th']} ")
                errs = errs + 1
            else:
                log(f"* {p.name} reached setpoint {curr} - readout {rd} = {abs(curr-rd)} < {feat['curr_th']}")
                ok = ok + 1

    time.sleep(10)
    cnt = 0
    for p in psa:
        log(f"****** {p.name} reached current:{p.get_current()} setting STBY ***")
        p.set_state("STANDBY")
        if p.wait(60) != 0:
            log(f"# {p.name} failed setting in STBY")
            errs = errs + 1
            continue

    log(f"* Result {ok}/{ok+errs} OK")

if __name__ == "__main__":
    main()