import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS, ophyd_ps_state, PowerSupplyState
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from .epik8s_device import epik8sDevice




class ZeroStandby(PowerSupplyState):
    def handle(self, ps):
        pr=f"{ps.name}[{ps._state_instance.state} {ps._setstate} {ps.last_state_set}]"
        if abs(ps.get_current())<=ps._th_stdby:
                if ps._verbose:
                    print(f"{pr} Current: {ps._current:.2f} < threshold {ps._th_stdby} putting in STANDBY ")
                ps.mode.put(ps.encodeStatus(ophyd_ps_state.STANDBY))
                ps.transition_to(waitStandby)
                ps.last_state_set = None

class waitStandby(PowerSupplyState):
        def handle(self, ps):
            pr=f"{ps.name}[{ps._state_instance.state} {ps._setstate} {ps.last_state_set}]"

            if ps._verbose:
                    print(f"{pr} Current: {ps._current:.2f} Stage {ps._state} duration {self.duration()}")
            if ps._state == ophyd_ps_state.STANDBY:
                ps.transition_to(StandbyState)
            if self.duration() > ps.timeout_mode_change/2:
                ps.mode.put(ps.encodeStatus(ophyd_ps_state.STANDBY))

            if self.duration() > ps.timeout_mode_change:
                print(f"## {pr} FAILED to GO IN STANDBY Current: {ps._current:.2f} Stage {ps._state} duration {self.duration()}")

                ps.last_state_set = ophyd_ps_state.STANDBY
                if ps._state == ophyd_ps_state.ON:
                    ps.transition_to(OnState)
                    
class OnState(PowerSupplyState):
    
    def handle(self, ps):
        ## handle change state
        pr=f"{ps.name}[{ps._state_instance.state} {ps._setstate} {ps.last_state_set} bipolar {ps._bipolar} polarity {ps._polarity}]"

        if ((ps._setstate == ophyd_ps_state.STANDBY) or (ps._setstate == ophyd_ps_state.OFF) or (ps._setstate == ophyd_ps_state.RESET)) and ps.last_state_set == None:
            ps.current.put(0)
            ps.transition_to(ZeroStandby)
        
        elif ps._state == ophyd_ps_state.ON:
            if ps._setpoint != None and ps.last_current_set == None:
                if abs(ps._setpoint - ps.get_current()) > ps._th_current:
                    if not ps._bipolar:
                        if ps._polarity!=None:
                            if (ps._setpoint>=0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                                if ps._verbose:
                                    print(f"{pr} Polarity mismatch detected. Transitioning to STANDBY.")
                                ps.current.put(0)
                                ps.transition_to(ZeroStandby)
                                return
                            ps.current.put(abs(ps._setpoint))
                            ps.last_current_set = ps._setpoint
                            if ps._verbose:
                                print(f"{pr} set current to {ps._setpoint}")
                    else:
                        ps.current.put(ps._setpoint)
                        ps.last_current_set=ps._setpoint
                        if ps._verbose:
                            print(f"{pr} Bipolar set current to {ps._setpoint}")
                        
        if ps._verbose > 2:      
            print(f"{pr} State: {ps._state} set:{ps._setstate}, Current: {ps._current} set:{ps._setpoint}, Polarity: {ps._polarity} ")

class StandbyState(PowerSupplyState):
    def handle(self, ps):
        ## if state on current under threshold
        pr=f"{ps.name}[{ps._state_instance.state} {ps._setstate} {ps.last_state_set} bipolar {ps._bipolar} polarity {ps._polarity}]"

        if ps._state == ophyd_ps_state.STANDBY:
            ## fix polarity
            ## fix state
            if(ps._setstate == ophyd_ps_state.RESET) and ps.last_state_set == None:
                if ps._verbose:
                    print(f"{pr} set mode to RESET")
                ps.mode.put(ps.encodeStatus(ophyd_ps_state.RESET))
                ps.last_state_set=ophyd_ps_state.RESET
                return

            if not(ps._bipolar):
                if (ps._setpoint!= None) and (ps.last_polarity_set==None):
                    
                    if(ps._setpoint>0 and ps._polarity==-1) or (ps._setpoint<0 and ps._polarity==1):
                        if ps._setpoint>0:
                            v= "POS"
                            ps.last_polarity_set=1
                        elif ps._setpoint<0:
                            v="NEG"
                            ps.last_polarity_set=-1

                        else:
                            ps.last_polarity_set=0
                            v= "OPN"


                        if ps._verbose:
                            print(f"{pr} set polarity to {v}")
                        ps.polarity.put(v)

                        return
                    # elif ps._setpoint==0:
                    #     if ps._verbose:
                    #         print(f"{pr} set polarity to 0")
                    #     ps.polarity.put("OPEN")
                    #     ps.last_polarity_set="OPEN"
                    #     return
            
            if(ps._setstate == ophyd_ps_state.ON) and ps.last_state_set == None :
                v= ps.encodeStatus(ophyd_ps_state.ON)
                if ps._verbose:
                    print(f"{pr} set mode to ON {v}")
                ps.mode.put(v)
                ps.last_state_set=ophyd_ps_state.ON

class OnInit(PowerSupplyState):
    def handle(self, ps):
        if ps._verbose:
            print(f"{ps.name}[{ps._state_instance.__class__.__name__}]")

        # if ps._state != None and ps._current!= None:
        #     if ps._state == ophyd_ps_state.ON:
        #         ps.transition_to(OnState)
        #     elif ps._state != ophyd_ps_state.UKNOWN:
        #         ps.transition_to(StandbyState)
            

            

class ErrorState(PowerSupplyState):
    def handle(self, ps):
        
        pr=f"{ps.name}[{ps._state_instance.state} {ps._setstate} {ps.last_state_set}]"
        print(f"{pr} Error encountered. Current: {ps._current:.2f}")
        
class OphydPSDante(OphydPS, epik8sDevice):
    current_rb = Cpt(EpicsSignalRO, ':current_rb')
    polarity_rb = Cpt(EpicsSignalRO, ':polarity_rb')
    mode_rb = Cpt(EpicsSignalRO, ':mode_rb')
    current = Cpt(EpicsSignal, ':current')
    polarity= Cpt(EpicsSignal, ':polarity')
    mode = Cpt(EpicsSignal, ':mode')

    def __init__(self, name, prefix, max=10, min=-10, bipolar=None, verbose=0, zero_error=1.5, sim_cycle=1, th_stdby=0.5, th_current=0.01, **kwargs):
        """
        Initialize the simulated power supply.

        :param uncertainty_percentage: Percentage to add random fluctuations to current.
        """
        OphydPS.__init__(self, name=name, min_current=min, max_current=max, verbose=verbose, **kwargs)
        epik8sDevice.__init__(
            self,
            prefix,
            read_attrs=None,
            configuration_attrs=None,
            name=name,
            parent=None,
            **kwargs
        )
        self._current = None
        self._polarity= None
        self._setpoint = None
        self._th_stdby=th_stdby # if less equal can switch to stdby
        self._th_current=th_current # The step in setting current
        self._bipolar = False
        self.last_polarity_set=None
        self.timeout_mode_change=20
        
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
        self.transition_to(OnInit)

        self.current_rb.subscribe(self._on_current_change)
        self.polarity_rb.subscribe(self._on_pol_change)
        self.mode_rb.subscribe(self._on_mode_change)
        ## access all variable to check if they exist
        self._current = self.current_rb.get()
        self._polarity= self.polarity_rb.get()
        self._setpoint= self.current.get()
        self._mode = self.mode.get()

        self._state=self.decodeStatus(self.mode_rb.get())
        self._mode = self.mode_rb.get()
        self._setpoint= self.current_rb.get()

        print(f"* creating Dante Mag {name} as {prefix} min={min},max={max} state: {self._state}")

        self.run()
        
    def _on_current_change(self, pvname=None, value=None, **kwargs):
        
        if not(self._bipolar) and (self._polarity != None) and (self._polarity<2 and self._polarity > -2):
            self._current = value*self._polarity
        else:
            self._current = value
        if self._verbose > 1:
         print(f"{self.name} current changed {value} setpoint: {self._setpoint}")
        self.on_current_change(self._current,self)

    def transition_to(self, new_state_class):
        """Transition to a new state."""
        self._state_instance = new_state_class()
        if self._verbose:
            print(f"[{self.name}] Transitioning to {self._state_instance.state}.")

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
        pr=f"{self.name}[{self._state_instance.state} {self._setstate} {self.last_state_set}]"

        if self._polarity == 3 and self._bipolar == False:
            self._bipolar = True
            print(f"{self.name} is bipolar")
        if self._verbose:
            print(f"{pr}  polarity changed {value} set state {self._setstate}")
        if self._polarity != self.last_polarity_set:
            print(f"{self.name} external change last polarity {self.last_polarity_set}")
            self._setpoint = self._current*self._polarity
            self.last_polarity_set = self._polarity
            
            
    def _on_mode_change(self, pvname=None, value=None, **kwargs):
        
        self._state=self.decodeStatus(value)
        self._mode = value
        pr=f"{self.name}[{self._state_instance.state} {self._setstate} {self.last_state_set}]"

        if self._verbose:
            print(f"{pr} mode changed {value} -> {self._state} setstate {self._setstate}")
        if self._state != self.last_state_set and self._state_instance.state!="waitStandby":  
            print(f"{self.name} external change last state {self.last_state_set}")
            self._setstate = self._state
            self.last_state_set = self._state

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
        self.last_current_set=None
        self.last_polarity_set=None

        """ setting the current."""
        pr=f"{self.name}[{self.__class__.__name__}] {self.name}[{self._state_instance.state} {self._state}]"

        super().set_current(value)  # Check against min/max limits
        print(f"{pr} setpoint current {value} bipolar {self._bipolar} polarity {self._polarity}")
        self._setpoint = value
        
    def wait(self,timeo) -> int:
        """Wait for setpoint reach with time, 0 wait indefinitively, return negative if timeout"""
        start_time = time.time()
        val=None
        if self._current != None and self._setpoint != None:
            val =abs(self._current - self._setpoint)
        if self._verbose:
            print (f"[{self.name}] wait {self._setstate} == {self._state} and ({self._current} - {self._setpoint})={val} < {self._th_current} in {timeo} sec.")
        while True:
            if self._current!=None and self._setpoint != None:
                if self._setstate == "STANDBY" and self._state == "STANDBY":
                    return 0
                if self._setstate == self._state and (abs(self._current - self._setpoint)<=self._th_current):
                    return 0
            else:
                if self._setstate == self._state:
                    return 0
            
            if timeo>0 and (time.time() - start_time > timeo):
                if self._verbose:
                    print (f"[{self.name}] ## wait {self._setstate} == {self._state} and ({self._current} - {self._setpoint})={val} < {self._th_current} in {timeo} sec.")
                return -1
            time.sleep(0.5)
    
    def set_state(self, state: ophyd_ps_state):    
        pr=f"{self.name}[{self.__class__.__name__}] {self.name}[{self._state_instance.state} {self._state}]"
        self.last_state_set=None
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
