from infn_ophyd_hal import PowerSupplyFactory,ophyd_ps_state
import time

def main():
    
    
    def current_change_callback(new_value,psa):
        print(f"[{psa.name} Current updated to: {new_value:.2f} A")

    def state_change_callback(new_state,psa):
        print(f"{psa.name} State updated to: {new_state}")
        if new_state == ophyd_ps_state.ERROR:
            
            print(f" {psa.name} Error Detected")
            if psa.get_current()!=0:
                print(f"## after ERROR current must be 0")
                exit(-1)
            
            psa.set_state(ophyd_ps_state.RESET)
            psa.set_current(10)


        if new_state == ophyd_ps_state.INTERLOCK:
            print(f" {psa.name} Interlock Detected, resetting")
            if ps.get_current()!=0:
                print(f"## after INTERLOCK current must be 0")
                exit(-1)
            psa.set_state(ophyd_ps_state.RESET)
            psa.set_current(11)
            
    ps = PowerSupplyFactory.create("sim",
        name="broken-sim",
        min_current=0.0,
        max_current=100.0,
        uncertainty_percentage=5.0,
        error_prob=0.2,
        interlock_prob=0.3
    )
    ps.on_current_change = current_change_callback
    ps.on_state_change = state_change_callback
    psi= [None] * 10
    for alim in range(0,9):
        psi[alim] =PowerSupplyFactory.create("sim",
            name="ideal-sim-"+str(alim),
            min_current=-100.0,
            max_current=100.0,
            uncertainty_percentage=0,
            error_prob=0.0,
            interlock_prob=0
        )
        psi[alim].on_current_change = current_change_callback
        psi[alim].on_state_change = state_change_callback
        
    
# Attach callbacks
    for alim in range(0,9):
        psi[alim].set_state("ON")
        val = ((alim+1)*10)*(-1 if (alim & 1) else 1)
        psi[alim].set_current(val)
        print(f"{psi[alim].name} setpoint to {val}")


    ps.set_current(10)

    ps.set_state("ON")
    ps.set_current(10)
    cnt=20

    try:
            time.sleep(10)
    finally:
        ps.stop()
        print(f"* {ps.name} reached  current:{ps.get_current()}")

        for alim in range(0,9):
            val = ((alim+1)*10)*(-1 if (alim & 1) else 1)

            if psi[alim].get_current() != val:
                print(f"Error {psi[alim].name} not get setpoint {val}!={psi[alim].get_current()}")
                exit(-2)
            else:
                print(f"* {psi[alim].name} reached set point {val} current:{psi[alim].get_current()}")
        for alim in range(0,9):
           psi[alim].stop() 


if __name__ == "__main__":
    main()