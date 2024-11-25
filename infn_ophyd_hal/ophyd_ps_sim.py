import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state


    
class OphydPSSim(OphydPS):
    def __init__(self, name, uncertainty_percentage=0.0, error_prob=0,interlock_prob=0,simcycle=.2,slope=10, **kwargs):
        """
        Initialize the simulated power supply.

        :param uncertainty_percentage: Percentage to add random fluctuations to current.
        """
        super().__init__(name=name, **kwargs)
        self._current = 0.0
        self._setpoint = 0.0

        self._state = ophyd_ps_state.OFF
        self.uncertainty_percentage = uncertainty_percentage
        self._run_thread = None
        self._running = False
        self._error_prob = error_prob
        self._interlock_prob=interlock_prob
        self._simcycle = simcycle
        self._slope=slope ## ampere/s
        self.run()

    def set_current(self, value: float):
        """Simulate setting the current."""
        if self._state != ophyd_ps_state.ON:
            print(f"[{self.name}] [sim] cannot change current to {value} A , powersupply is not in ON")
            return
        
        super().set_current(value)  # Check against min/max limits
        
        self._setpoint = value
        # if(changed):
        #     print(f"[{self.name}] [sim] changed current to {value} A")
        #     self.on_current_change(value)

    def set_state(self, state: ophyd_ps_state):
        """Simulate setting the state."""
        if self._state == ophyd_ps_state.INTERLOCK or self._state == ophyd_ps_state.ERROR:
            if state==ophyd_ps_state.RESET:
                state =  ophyd_ps_state.ON
            elif state==ophyd_ps_state.OFF:
                state =  ophyd_ps_state.OFF 
            else:
                print(f"[{self.name}] [sim] a \"RESET\" | \"OFF\" must done in the state:\"{state}\"")
                self._current=0
                self.on_current_change(self._current,self)

                return
        


        if state != ophyd_ps_state.ON:
            self._current=0
            self.on_current_change(self._current,self)

            
        changed=(self._state != state)

        self._state = state
        if changed:
            print(f"[{self.name}] [sim] simulated changed state to \"{state}\"")
            self.on_state_change(state,self)

    def get_current(self) -> float:
        """Get the simulated current with optional uncertainty."""
        
        return self._current

    def get_state(self) -> ophyd_ps_state:
        """Get the simulated state."""
        return self._state

    def run(self):
        """Start a background run."""
        self._running = True
        self._run_thread = Thread(target=self._run_device, daemon=True)
        self._run_thread.start()

    def stop(self):
        """Stop the run."""
        self._running = False
        if self._run_thread is not None:
            self._run_thread.join()

    def _run_device(self):
        oldcurrent=0
        """Simulate periodic updates to current and state."""
        while self._running:
            try:
                                
                    
                if self.get_state() == ophyd_ps_state.ON:
                    increment= self._slope*self._simcycle
                    fluctuation = self._current * self.uncertainty_percentage / 100.0
                    
                    delta=self._setpoint - self._current 
                    if abs(delta)<increment: 
                        self._current=self._current +delta
                    else:
                        if delta>0:
                            self._current=self._current +increment      
                        else:
                            self._current=self._current - increment      

                    
                    self._current= self._current+ random.uniform(-fluctuation, fluctuation)
                
                    ## during ON simulate errors and interlocks
                    if random.random() < self._interlock_prob:
                        self._current=0
                        self.on_current_change(self._current,self)
                        self.set_state(ophyd_ps_state.INTERLOCK)
                    
                    if random.random() < self._error_prob:
                        self._current=0
                        self.on_current_change(self._current,self)
                        self.set_state(ophyd_ps_state.ERROR)
                if oldcurrent!=self._current:
                    self.on_current_change(self._current,self)

                oldcurrent=self._current        
                time.sleep(self._simcycle) 
            except Exception as e:
                print(f"Simulation error: {e}")
