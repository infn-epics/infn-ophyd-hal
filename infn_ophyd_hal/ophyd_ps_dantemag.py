import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state,PowerSupplyState
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO,PositionerBase




class ZeroStandby(PowerSupplyState):
    def handle(self, ps):
        print(f"State {ps._state_instance.__class__.__name__}")
        if abs(ps.get_current()>ps._th_stdby):
            print(f"[{ps.name}] Current must be less of {ps._th_stdby} A : ON, Current: {ps._current:.2f}")
            print(f"[{ps.name}] set current to 0")
            ps.current.put(0)
            return
        else:
            print(f"[{ps.name}] Current: {ps._current:.2f} putting in STANDBY ")
            ps.mode.put(ps.encodeStatus(ophyd_ps_state.STANDBY))

class OnState(PowerSupplyState):
    def handle(self, ps):
        ## handle change state
        if ps._setstate == ophyd_ps_state.STANDBY:
            ps.transition_to(ZeroStandby)
        
        elif ps._setstate == ophyd_ps_state.ON:
            if abs(ps._setpoint - ps.get_current()) > ps._th_current:
                if not ps._bipolar:
                    if (ps._setpoint>=0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                        print(f"[{ps.name}] Polarity mismatch detected. Transitioning to STANDBY.")
                        ps.transition_to(ZeroStandby)
                        return
                    ps.current.put(abs(ps._setpoint))
                else:
                    ps.current.put(ps._setpoint)
                print(f"[{ps.name}] set current to {ps._setpoint}")

                    
        print(f"[{ps.name}] State: {ps._state} set:{ps._setstate}, Current: {ps._current:.2f} set:{ps._setpoint:.2f}, Polarity: {ps._polarity} ")

class StandbyState(PowerSupplyState):
    def handle(self, ps):
        ## if state on current under threshold    
        if ps._state == ophyd_ps_state.STANDBY:
            ## fix polarity
            ## fix state
            if ps._setpoint==0:
                print(f"[{ps.name}] set polarity to 0")

                ps.polarity.put(0)
            elif(ps._setpoint>0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                v= "POS" if ps._setpoint>=0 else "NEG"
                print(f"[{ps.name}] set polarity to {v}")

                ps.polarity.put(v)
            elif(ps._setstate == ophyd_ps_state.ON):
                v= ps.encodeStatus(ophyd_ps_state.ON)
                print(f"[{ps.name}] set mode to ON {v}")
                ps.mode.put(v)

           
class OnInit(PowerSupplyState):
    def handle(self, ps):
        if ps._state == ophyd_ps_state.ON:
            ps.transition_to(OnState)
        if ps._state != ophyd_ps_state.UKNOWN:
            ps.transition_to(StandbyState)
            

            

class ErrorState(PowerSupplyState):
    def handle(self, ps):
        print(f"[{ps.name}] Error encountered. Current: {ps._current:.2f}")
        
class OphydPSDante(OphydPS,Device):
    current_rb = Cpt(EpicsSignalRO, ':current_rb')
    polarity_rb = Cpt(EpicsSignalRO, ':polarity_rb')
    mode_rb = Cpt(EpicsSignalRO, ':mode_rb')
    current = Cpt(EpicsSignal, ':current')
    polarity= Cpt(EpicsSignal, ':polarity')
    mode = Cpt(EpicsSignal, ':mode')

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

        self._state_instance=OnInit()
        self.current_rb.subscribe(self._on_current_change)
        self.polarity_rb.subscribe(self._on_pol_change)
        self.mode_rb.subscribe(self._on_mode_change)

        self.transition_to(OnInit)
        print(f"* creating Dante Mag {name} as {prefix}")

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

    def encodeStatus(self,value):
        if value == ophyd_ps_state.ON:
            return "OPER"
        elif value == ophyd_ps_state.RESET:
            return "RST"
        ## STANDBY and other
        return "STBY"
        
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
        if(self._state==ophyd_ps_state.ON):
            self.transition_to(OnState)
        elif (self._state==ophyd_ps_state.ON) or (ophyd_ps_state.STANDBY):
            self.transition_to(StandbyState)
        else:
            self.transition_to(ErrorState)


            
    def set_current(self, value: float):
        """ setting the current."""
        
        super().set_current(value)  # Check against min/max limits
        print(f"{self.name} setpoint current {value}")
        
        self._setpoint = value
        

    def set_state(self, state: ophyd_ps_state):        
        self._setstate = state
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
        print(f"* controlling dante ps {self.name}")

        """Simulate periodic updates to current and state."""
        while self._running:
            try:
                
                self._state_instance.handle(self)

                time.sleep(self._simcycle) 
            except Exception as e:
                print(f"Run error: {e}")
                self._running= False
        print(f"* end controlling dante ps {self.name} ")
