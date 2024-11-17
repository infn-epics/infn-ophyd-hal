from enum import Enum

# Enum for power supply states
class ophyd_ps_state(str, Enum):
    OFF = "OFF"
    ON = "ON"
    STANDBY = "STANDBY"
    RESET = "RESET"
    INTERLOCK = "INTERLOCK"
    ERROR = "ERROR"

# Base class for power supply
class OphydPS():
    def __init__(self, name, min_current=-10.000, max_current=10000, **kwargs):
        self.min_current = min_current
        self.max_current = max_current
        self.name = name

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
        print(f"{self.name} to ovverride [OphydPS:set_state] Current changed to: {ophyd_ps_state}")
           

    def get_current(self) -> float:
        """Get the current value."""
        print(f"{self.name} to ovverride [OphydPS:get_current]")

        return 0

    def get_state(self) -> ophyd_ps_state:
        """Get the state value."""
        print(f"{self.name} to ovverride [OphydPS:get_state]")

        return ophyd_ps_state.OFF

    def on_current_change(self, new_value):
        """Callback for current change."""
        print(f"{self.name} [OphydPS:Callback] Current changed to: {new_value}")

    def on_state_change(self, new_state):
        """Callback for state change."""
        print(f"{self.name} [OphydPS:Callback] State changed to: {new_state}")