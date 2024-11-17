from infn_ophyd_hal import OphydPSSim,ophyd_ps_state
import time

def main():
    ps = OphydPSSim(
        name="broken-sim",
        min_current=0.0,
        max_current=100.0,
        uncertainty_percentage=5.0,
        error_prob=0.2,
        interlock_prob=0.3
    )
    
    ps2 = OphydPSSim(
        name="ideal-sim",
        min_current=0.0,
        max_current=100.0,
        uncertainty_percentage=0,
        error_prob=0.0,
        interlock_prob=0
    )
    
    
    # Define callbacks for current and state changes
    def current_change_callback(new_value):
        print(f"[Main Callback] Current updated to: {new_value:.2f} A")

    def state_change_callback(new_state):
        print(f"[Main Callback] State updated to: {new_state}")
        if new_state == ophyd_ps_state.ERROR:
            
            print(f"Error Detected")
            if ps.get_current()!=0:
                print(f"## after ERROR current must be 0")
                return -1
            
            ps.set_state(ophyd_ps_state.RESET)
            ps.set_current(10)


        if new_state == ophyd_ps_state.INTERLOCK:
            print(f"Interlock Detected, resetting")
            if ps.get_current()!=0:
                print(f"## after INTERLOCK current must be 0")
                return -1
            ps.set_state(ophyd_ps_state.RESET)
            ps.set_current(11)

            


    # Attach callbacks
    ps.on_current_change = current_change_callback
    ps.on_state_change = state_change_callback
# Attach callbacks
    ps2.on_current_change = current_change_callback
    ps2.on_state_change = state_change_callback
    ps.start_simulation()
    ps2.start_simulation()
    ps2.set_state("ON")

    ps.set_current(10)

    ps.set_state("ON")
    ps.set_current(10)
    cnt=20

    try:
        while cnt:
            ps2.set_current(cnt)
            if ps2.get_current()!=cnt:
                print(f"## {ps2.name} set {cnt}!= readout {ps2.get_current()}")
                return -2

            # Run simulation for 10 seconds
            cnt = cnt-1
            time.sleep(2)
    finally:
        ps.stop_simulation()
        ps2.stop_simulation()


if __name__ == "__main__":
    main()