import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state,PowerSupplyState
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO,PositionerBase




class ZeroStandby(PowerSupplyState):
    def handle(self, ps):
        pr=f"{ps.name}[{ps._state_instance.__class__.__name__} {ps._state}]"
        if abs(ps.get_current())>ps._th_stdby:
            if self.last_current_set!=0:
                if ps._verbose:
                    print(f"{pr} Current must be less of {ps._th_stdby} A : ON, Current: {ps._current:.2f}")
                    print(f"{pr} set current to 0")
                ps.current.put(0)
                self.last_current_set=0
            
                
            return
        else:
            if self.last_state_set!=ophyd_ps_state.STANDBY:
                if ps._verbose:
                    print(f"{pr} Current: {ps._current:.2f} < threshold {ps._th_stdby} putting in STANDBY ")
                ps.mode.put(ps.encodeStatus(ophyd_ps_state.STANDBY))
                self.last_state_set=ophyd_ps_state.STANDBY

class OnState(PowerSupplyState):
    
    def handle(self, ps):
        ## handle change state
        pr=f"{ps.name}[{ps._state_instance.__class__.__name__} {ps._state}]"

        if (ps._setstate == ophyd_ps_state.STANDBY) or (ps._setstate == ophyd_ps_state.OFF) or (ps._setstate == ophyd_ps_state.RESET):
            ps.transition_to(ZeroStandby)
        
        elif ps._state == ophyd_ps_state.ON:
            if ps._setpoint != None:
                if abs(ps._setpoint - ps.get_current()) > ps._th_current:
                    if not ps._bipolar:
                        if ps._polarity!=None:
                            if (ps._setpoint>=0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                                if ps._verbose:
                                    print(f"{pr} Polarity mismatch detected. Transitioning to STANDBY.")
                                ps.transition_to(ZeroStandby)
                                return
                            if self.last_current_set !=ps._setpoint:
                                ps.current.put(abs(ps._setpoint))
                                if ps._verbose:
                                    print(f"{pr} set current to {ps._setpoint}")
                                self.last_current_set = ps._setpoint
                    else:
                        ps.current.put(ps._setpoint)
                        if ps._verbose:
                            print(f"{pr} Bipolar set current to {ps._setpoint}")

        if ps._verbose > 2:      
            print(f"{pr} State: {ps._state} set:{ps._setstate}, Current: {ps._current} set:{ps._setpoint}, Polarity: {ps._polarity} ")

class StandbyState(PowerSupplyState):
    def handle(self, ps):
        ## if state on current under threshold
        pr=f"{ps.name}[{ps._state_instance.__class__.__name__} {ps._state}->{ps._setstate}] "

        if ps._state == ophyd_ps_state.STANDBY:
            ## fix polarity
            ## fix state
            if(ps._setstate == ophyd_ps_state.RESET):
                if self.last_state_set!=ophyd_ps_state.RESET:
                    if ps._verbose:
                        print(f"{pr} set mode to RESET")
                    ps.mode.put(ps.encodeStatus(ophyd_ps_state.RESET))
                    self.last_state_set=ophyd_ps_state.RESET
                return

            if not(ps._bipolar):
                if (ps._setpoint!= None):
                    if ps._setpoint==0:
                        if self.last_state_set!="OPEN":
                            if ps._verbose:
                                print(f"{pr} set polarity to 0")
                            ps.polarity.put("OPEN")
                            self.last_state_set="OPEN"

                        return
                    elif(ps._setpoint>0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                        v= "POS" if ps._setpoint>=0 else "NEG"
                        if self.last_state_set!=v:
                            if ps._verbose:
                                print(f"{pr} set polarity to {v}")
                            ps.polarity.put(v)
                            self.last_state_set=v
                        return
            
            if(ps._setstate == ophyd_ps_state.ON):
                v= ps.encodeStatus(ophyd_ps_state.ON)
                if self.last_state_set !=ps._setstate:
                    if ps._verbose:
                        print(f"{pr} set mode to ON {v}")
                    ps.mode.put(v)
                    self.last_state_set=ps._setstate

class OnInit(PowerSupplyState):
    def handle(self, ps):
        if ps._verbose:
            print(f"{ps.name}[{ps._state_instance.__class__.__name__}]")

        if ps._state != None and ps._current!= None:
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

    def __init__(self, name,prefix,max=10,min=-10,bipolar=None,verbose=0,zero_error=1.5,sim_cycle=1,th_stdby=0.5,th_current=0.01, **kwargs):
        """
        Initialize the simulated power supply.

        :param uncertainty_percentage: Percentage to add random fluctuations to current.
        """
        OphydPS.__init__(self,name=name, min_current=min,max_current=max,verbose=verbose,**kwargs)
        Device.__init__(self,prefix, read_attrs=None,
                         configuration_attrs=None,
                         name=name, parent=None, **kwargs)
        self._current = None
        self._polarity= None
        self._setpoint = None
        self._th_stdby=th_stdby # if less equal can switch to stdby
        self._th_current=th_current # The step in setting current
        self._bipolar = False

        if bipolar:
            self._bipolar = bipolar
            
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
        
        if not(self._bipolar) and (self._polarity != None) and (self._polarity<2 and self._polarity > -2):
            self._current = value*self._polarity
        else:
            self._current = value
        if self._verbose > 1:
         print(f"{self.name} current changed {value} -> {self._current}")
        self.on_current_change(self._current,self)

    def transition_to(self, new_state_class):
        """Transition to a new state."""
        self._state_instance = new_state_class()
        if self._verbose:
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
        if self._verbose:
            print(f"{self.name} polarity changed {value}")
    def _on_mode_change(self, pvname=None, value=None, **kwargs):
        
        self._state=self.decodeStatus(value)
        self._mode = value
        if self._verbose:
            print(f"{self.name} mode changed {value} -> {self._state}")

        self.on_state_change(self._state,self)
        if(self._state==ophyd_ps_state.ON):
            self.transition_to(OnState)
        elif (self._state==ophyd_ps_state.OFF) or (self._state==ophyd_ps_state.STANDBY):
            self.transition_to(StandbyState)
        else:
            self.transition_to(ErrorState)


    def get_features(self) -> dict:
        f=super().get_features()
        f['zero_th']=self._th_stdby # if less equal can switch to stdby
        f['curr_th']=self._th_current
        return f
       
    def set_current(self, value: float):
        """ setting the current."""
        pr=f"{self.name}[{self.__class__.__name__}] {self.name}[{self._state_instance.__class__.__name__} {self._state}]"

        super().set_current(value)  # Check against min/max limits
        print(f"{pr} setpoint current {value} ")
        self._state_instance.last_current_set=None
        self._setpoint = value
        
    def wait(self,timeo) -> int:
        """Wait for setpoint reach with time, 0 wait indefinitively, return negative if timeout"""
        start_time = time.time()
        val=None
        if self._current != None and self._setpoint != None:
            val =abs(self._current - self._setpoint)
        if self._verbose:
            print (f"wait {self._setstate} == {self._state} and ({self._current} - {self._setpoint})={val} < {self._th_current} in {timeo} sec.")
        while True:
            if self._current!=None and self._setpoint != None:
                if self._setstate == self._state and (abs(self._current - self._setpoint)<=self._th_current):
                    return 0
            else:
                if self._setstate == self._state:
                    return 0
            
            if timeo>0 and (time.time() - start_time > timeo):
                return -1
            time.sleep(0.5)
    
    def set_state(self, state: ophyd_ps_state):    
        pr=f"{self.name}[{self.__class__.__name__}] {self.name}[{self._state_instance.__class__.__name__} {self._state}]"
        # self._state_instance.last_state_set=None
        # self._state_instance.last_current_set=None

        self._setstate = state
        print(f"{pr} state setpoint \"{state}\"")

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
        print(f"* controlling dante ps {self.name}")

        """periodic updates to current and state."""
        while self._running:
          #  try:
                
                self._state_instance.handle(self)

                time.sleep(self._simcycle) 
         #   except Exception as e:
         #       print(f"Run error: {e}")
         #       self._running= False
        print(f"* end controlling dante ps {self.name} ")
