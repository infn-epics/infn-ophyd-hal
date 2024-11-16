from infn_ophyd_hal import OphydPSSim,ophyd_ps_state
import time

def main():
    ps = OphydPSSim(
        name="sim_ps",
        min_current=0.0,
        max_current=100.0,
        uncertainty_percentage=5.0,
        error_prob=0.2,
        interlock_prob=0.3
    )
    
    
    # Define callbacks for current and state changes
    def current_change_callback(new_value):
        print(f"[Main Callback] Current updated to: {new_value:.2f} A")

    def state_change_callback(new_state):
        print(f"[Main Callback] State updated to: {new_state}")
        if new_state == ophyd_ps_state.ERROR:
            print(f"Error Detected, resetting")
            ps.set_state(ophyd_ps_state.RESET)

        if new_state == ophyd_ps_state.INTERLOCK:
            print(f"Interlock Detected, resetting")
            ps.set_state(ophyd_ps_state.RESET)
            


    # Attach callbacks
    ps.on_current_change = current_change_callback
    ps.on_state_change = state_change_callback

    ps.start_simulation()
    ps.set_current(10)
    
    try:
        # Run simulation for 10 seconds
        time.sleep(10)
    finally:
        ps.stop_simulation()

if __name__ == "__main__":
    main()