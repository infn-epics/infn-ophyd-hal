from enum import Enum
from abc import ABC, abstractmethod
import time

# Enum for power supply states
class ophyd_ps_state(str, Enum):
    OFF = "OFF"
    ON = "ON"
    STANDBY = "STANDBY"
    RESET = "RESET"
    INTERLOCK = "INTERLOCK"
    ERROR = "ERROR"
    UKNOWN = "UKNOWN"

# Base class for power supply
class OphydPS():
    def __init__(self, name, min_current=-10.000, max_current=10, verbose=0, **kwargs):
        self.min_current = min_current
        self.max_current = max_current
        self.name = name
        self._verbose=verbose
        self.last_current_set = None
        self.last_state_set = None

    def set_current(self, value: float):
        """
        Set the current of the power supply.
        Ensure the value is within the specified limits.
        """
        if value < self.min_current or value > self.max_current:
            raise ValueError(
                f"Current {value} is out of bounds! Must be between {self.min_current} and {self.max_current}."
            )

    def set_state(self, state: ophyd_ps_state):
        """
        Set the state of the power supply.
        Should be overridden in derived classes for hardware-specific logic.
        """ 
        print(f"{self.name} to override [OphydPS:set_state] Current changed to: {ophyd_ps_state}")
           
    def run(self):
        """Run machine state"""
        print(f"{self.name} to override [OphydPS:run]")
        return 0
    def stop(self):
        """Stop machine state"""
        print(f"{self.name} to override [OphydPS:stop]")
        
    def get_current(self) -> float:
        """Get the current value."""
        print(f"{self.name} to override [OphydPS:get_current]")

        return 0
    
    def get_features(self) -> dict:
        """Get the features value."""
        f={'max':self.max_current,'min':self.min_current,'zero_th':0,'curr_th':0,'slope':self.max_current/10.0}
        return f

    def wait(self,timeo) -> int:
        """Wait for setpoint reach with time, 0 wait indefinitively, return negative if timeout"""
        return 0

    def get_state(self) -> ophyd_ps_state:
        """Get the state value."""
        print(f"{self.name} to override [OphydPS:get_state]")

        return ophyd_ps_state.OFF

    def on_current_change(self, new_value,*args):
        """Callback for current change."""
        print(f"{self.name} [OphydPS:Callback] Current changed to: {new_value}")

    def on_state_change(self, new_state,*args):
        """Callback for state change."""
        print(f"{self.name} [OphydPS:Callback] State changed to: {new_state}")
        
        
class PowerSupplyState(ABC):
    """Abstract base class for power supply states."""
    def __init__(self):
        # Initialize the state
        self.state = self.__class__.__name__
        self.start = time.time()

    def duration(self):
        return time.time() - self.start
    
    @abstractmethod
    def handle(self, ps):
        """Perform actions specific to the current state."""
        pass
    
class PowerSupplyFactory:
    _registry = {}

    @classmethod
    def register_type(cls, supply_type, constructor):
        print(f"* registered type {supply_type}")
        cls._registry[supply_type] = constructor

    @classmethod
    def create(cls, supply_type, name, *args, **kwargs):
        if supply_type not in cls._registry:
            raise ValueError(f"Unknown PowerSupply type: {supply_type}")
        return cls._registry[supply_type](name, *args, **kwargs)