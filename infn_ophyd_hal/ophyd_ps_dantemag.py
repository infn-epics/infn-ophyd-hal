import time
import random
from threading import Thread
from infn_ophyd_hal import OphydPS,ophyd_ps_state
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO,PositionerBase


class OphydPSDante(OphydPS,Device):
    current_rb = Cpt(EpicsSignalRO, ':current_rb')
    polarity_rb = Cpt(EpicsSignalRO, ':polarity_rb')
    mode_rb = Cpt(EpicsSignalRO, ':mode_rb')
  #  current = Cpt(EpicsSignal, ':current')
  #  polarity= Cpt(EpicsSignal, ':polarity')
  #  mode = Cpt(EpicsSignal, ':mode')

    def __init__(self, name,prefix,max=100,min=-100,zero_error=1.5,sim_cycle=1, **kwargs):
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
        self._bipolar = False
        self._zero_error= zero_error ## error on zero
        self._setstate = ophyd_ps_state.UKNOWN
        self._state = ophyd_ps_state.UKNOWN
        self._mode=0
        self._simulation_thread = None
        self._running = False
        self._simcycle=sim_cycle
        self.current_rb.subscribe(self._on_current_change)
        self.polarity_rb.subscribe(self._on_pol_change)
        self.mode_rb.subscribe(self._on_mode_change)
        self.start_simulation()
        
    def _on_current_change(self, pvname=None, value=None, **kwargs):
    
        if self._polarity<2 and self._polarity > -2:
            self._current = value*self._polarity
        else:
            self._current = value
        
        print(f"{self.name} current changed {value} -> {self._current}")
        self.on_current_change(self._current,self)


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
        print(f"{self.name} set current {value}")
        
        self._setpoint = value
        

    def set_state(self, state: ophyd_ps_state):
        if state== ophyd_ps_state.ON:
            self._setstate = state

        elif state == ophyd_ps_state.OFF or state == ophyd_ps_state.STANDBY:
            self._setstate = state

        
        print(f"[{self.name}] set state to \"{state}\"")

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
        oldcurrent=0
        oldstate= ophyd_ps_state.UKNOWN
        """Simulate periodic updates to current and state."""
        while self._running:
            try:
                # if self._state != ophyd_ps_state.UKNOWN):
                #     if self._state != self._setpoint:
                #         if self._state == ophyd_ps_state.STANDBY and self._setpoint== ophyd_ps_state.ON:
                #             print(f" current state {self._state} -> settinf for {self._setpoint}")
                #             # self.mode.put(2)
                        
                #         if self._state == ophyd_ps_state.ON and self._setpoint== ophyd_ps_state.STANDBY:

                #             if abs(self._current)>=0 and abs(self._current)<self._zero_error:
                #                 print(f" current state {self._state} current {self._current} -> setting for {self._setpoint}")
                #             #  self.mode.put(1)
                #             else:
                #                 print(f" current state {self._state} current {self._current}> {self._zero_error} setting current to zero")
                #             #  self.current.put(0)
                #     elif self._state == ophyd_ps_state.ON:
                #         if self._setpoint!= self._current:
                #             if self._bipolar:
                #                 self.current.put(self._setpoint)
                #             else:
                #                 if (self._setpoint >=0 and self._current>=0) or (self._setpoint <0 and self._current==-1):
                #                     # concordi
                #                     self.current.put(self._setpoint)
                #                 else:
                #                     self.set_state(ophyd_ps_state.STANDBY) ## put stby


                
                
                time.sleep(self._simcycle) 
            except Exception as e:
                print(f"Simulation error: {e}")
