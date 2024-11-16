import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state

class OphydPSSim(OphydPS):
    def __init__(self, name, uncertainty_percentage=0.0, error_prob=0,interlock_prob=0,simcycle=1, **kwargs):
        """
        Initialize the simulated power supply.

        :param uncertainty_percentage: Percentage to add random fluctuations to current.
        """
        super().__init__(name=name, **kwargs)
        self._current = 0.0
        self._state = ophyd_ps_state.OFF
        self.uncertainty_percentage = uncertainty_percentage
        self._simulation_thread = None
        self._running = False
        self._error_prob = error_prob
        self._interlock_prob=interlock_prob
        self._simcycle = simcycle

    def set_current(self, value: float):
        """Simulate setting the current."""
        super().set_current(value)  # Check against min/max limits
        self._current = value
        print(f"Simulated setting current to {value} A")
        self.on_current_change(value)

    def set_state(self, state: ophyd_ps_state):
        """Simulate setting the state."""
        if state==ophyd_ps_state.RESET:
            if self._state == ophyd_ps_state.INTERLOCK or self._state == ophyd_ps_state.ERROR:
                state =  ophyd_ps_state.ON

        self._state = state
        
        print(f"Simulated setting state to {state}")
        self.on_state_change(state)

    def get_current(self) -> float:
        """Get the simulated current with optional uncertainty."""
        
        return self._current

    def get_state(self) -> ophyd_ps_state:
        """Get the simulated state."""
        return self._state

    def start_simulation(self):
        """Start a background simulation."""
        self._running = True
        self._simulation_thread = Thread(target=self._simulate_device, daemon=True)
        self._simulation_thread.start()

    def stop_simulation(self):
        """Stop the simulation."""
        self._running = False
        if self._simulation_thread is not None:
            self._simulation_thread.join()

    def _simulate_device(self):
        """Simulate periodic updates to current and state."""
        while self._running:
            try:

                new_current = self._current
                if random.random() < self._error_prob:
                    self.set_state(ophyd_ps_state.ERROR)

                if random.random() < self._interlock_prob:
                    self.set_state(ophyd_ps_state.INTERLOCK)
                    
                if self.get_state() != ophyd_ps_state.ON:
                    new_current=0
                else:
                    fluctuation = new_current * self.uncertainty_percentage / 100.0
                    new_current= new_current+ random.uniform(-fluctuation, fluctuation)
                    self.set_current(new_current)

                
                    

                time.sleep(self._simcycle) 
            except Exception as e:
                print(f"Simulation error: {e}")
