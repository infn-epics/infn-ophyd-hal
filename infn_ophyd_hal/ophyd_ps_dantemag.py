import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state,PowerSupplyState
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO,PositionerBase





class OnState(PowerSupplyState):
    def handle(self, ps):
        if ps._setstate == ophyd_ps_state.STANDBY:
            ps.transition_to(StandbyState())
        elif ps._state == ophyd_ps_state.ON:
            ## handle current
            if not ps._bipolar:
                if (ps._setpoint>=0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                    print(f"[{ps.name}] Polarity mismatch detected. Transitioning to STANDBY.")
                    ps.transition_to(StandbyState())
                    return
            if abs(ps._setpoint - ps.get_current()) > ps._th_current:
                    ps.current.put(ps._setpoint)
            

        print(f"[{ps.name}] State: ON, Current: {ps._current:.2f}")

class StandbyState(PowerSupplyState):
    def handle(self, ps):
        ## if state on current under threshold
        if ps._state == ophyd_ps_state.ON:
            if abs(ps.get_current()>ps._th_stdby):
                print(f"[{ps.name}] Current must be less of {ps._th_stdby} A : ON, Current: {ps._current:.2f}")
                ps.current.put(0)
            else:
                print(f"[{ps.name}] Current: {ps._current:.2f} putting in STANDBY ")
                ps.state.put(ophyd_ps_state.STANDBY)
        elif ps._state == ophyd_ps_state.STANDBY:
            ## fix polarity
            ## fix state
            if ps._setpoint==0:
                ps.polarity.put(0)
            elif(ps._setpoint>0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                ps.polarity.put(1 if ps._setpoint>=0 else -1)
            elif(ps._setstate == ophyd_ps_state.ON):
                ps.state.put(ophyd_ps_state.ON)
                ps.transition_to(OnState())

           
class OnInit(PowerSupplyState):
    def handle(self, ps):
        if self._state == ophyd_ps_state.ON:
            ps.transition_to(OnState())
        if self._state != ophyd_ps_state.UKNOWN:
            ps.transition_to(StandbyState())
            

            

class ErrorState(PowerSupplyState):
    def handle(self, ps):
        print(f"[{ps.name}] Error encountered. Current: {ps._current:.2f}")
        
class OphydPSDante(OphydPS,Device):
    current_rb = Cpt(EpicsSignalRO, ':current_rb')
    polarity_rb = Cpt(EpicsSignalRO, ':polarity_rb')
    mode_rb = Cpt(EpicsSignalRO, ':mode_rb')
  #  current = Cpt(EpicsSignal, ':current')
  #  polarity= Cpt(EpicsSignal, ':polarity')
  #  mode = Cpt(EpicsSignal, ':mode')

    def __init__(self, name,prefix,max=100,min=-100,zero_error=1.5,sim_cycle=1,th_stdby=0.5,th_current=0.01, **kwargs):
        """
        Initialize the simulated power supply.

        :param uncertainty_percentage: Percentage to add random fluctuations to current.
        """
        OphydPS.__init__(self,name=name, **kwargs)
        Device.__init__(self,prefix, read_attrs=None,
                         configuration_attrs=None,
                         name=name, parent=None, **kwargs)
        self._current = 0.0
        self._polarity=-100
        self._setpoint = 0.0
        self._th_stdby=th_stdby # if less equal can switch to stdby
        self._th_current=th_current # The step in setting current

        self._bipolar = False
        self._zero_error= zero_error ## error on zero
        self._setstate = ophyd_ps_state.UKNOWN
        self._state = ophyd_ps_state.UKNOWN
        self._mode=0
        self._run_thread = None
        self._running = False
        self._simcycle=sim_cycle
        self.current_rb.subscribe(self._on_current_change)
        self.polarity_rb.subscribe(self._on_pol_change)
        self.mode_rb.subscribe(self._on_mode_change)
        self.transition_to(OnInit())
        self.run()
        
    def _on_current_change(self, pvname=None, value=None, **kwargs):
    
        if self._polarity<2 and self._polarity > -2:
            self._current = value*self._polarity
        else:
            self._current = value
        
        print(f"{self.name} current changed {value} -> {self._current}")
        self.on_current_change(self._current,self)

    def transition_to(self, new_state_class):
        """Transition to a new state."""
        self._state_instance = new_state_class()
        print(f"[{self.name}] Transitioning to {self._state_instance.__class__.__name__}.")

    def decodeStatus(self,value):
        if value == 0:
            return ophyd_ps_state.OFF
        elif (value == 1) or (value == 5):
            return ophyd_ps_state.STANDBY
        elif (value == 2) or (value == 6):
            return ophyd_ps_state.ON
        elif value == 3:
            return ophyd_ps_state.INTERLOCK
        return ophyd_ps_state.ERROR
        
    def _on_pol_change(self, pvname=None, value=None, **kwargs):
        self._polarity = value
        if self._polarity == 3 and self._bipolar == False:
            self._bipolar = True
            print(f"{self.name} is bipolar")

            
        print(f"{self.name} polarity changed {value}")
    def _on_mode_change(self, pvname=None, value=None, **kwargs):
        
        self._state=self.decodeStatus(value)
        self._mode = value
        print(f"{self.name} mode changed {value} -> {self._state}")
        self.on_state_change(self._state,self)
            
    def set_current(self, value: float):
        """ setting the current."""
        
        super().set_current(value)  # Check against min/max limits
        print(f"{self.name} setpoint current {value}")
        
        self._setpoint = value
        

    def set_state(self, state: ophyd_ps_state):
        if self._state != state:
            if state ==ophyd_ps_state.STANDBY:
                self.transition_to(StandbyState)
                
        if state== ophyd_ps_state.ON:
            self._setstate = state

        elif state == ophyd_ps_state.OFF or state == ophyd_ps_state.STANDBY:
            self._setstate = state
        elif state == ophyd_ps_state.RESET
            print(f"[{self.name}] \"{state}\" not implemented")
            return


        print(f"[{self.name}] state setpoint \"{state}\"")

    def get_current(self) -> float:
        """Get the simulated current with optional uncertainty."""
        
        return self._current

    def get_state(self) -> ophyd_ps_state:
        """Get the simulated state."""
        return self._state

    def run(self):
        """Start a background simulation."""
        self._running = True
        self._run_thread = Thread(target=self._run_device, daemon=True)
        self._run_thread.start()

    def stop(self):
        """Stop run """
        self._running = False
        if self._run_thread is not None:
            self._run_thread.join()

    def _run_device(self):
        oldcurrent=0
        oldstate= ophyd_ps_state.UKNOWN
        """Simulate periodic updates to current and state."""
        while self._running:
            try:
                
                self._state_instance.handle(self)

                time.sleep(self._simcycle) 
            except Exception as e:
                print(f"Simulation error: {e}")
