from typing import Union

from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO
from .epik8s_device import epik8sDevice

from infn_ophyd_hal import OphydPS, ophyd_ps_state


class OphydPSUnimag(OphydPS, epik8sDevice):
    """
    Generic UNIMAG magnet power supply interface using straightforward PVs:

    - CURRENT_RB (RO): $(P):$(R):CURRENT_RB
    - CURRENT_SP (RW): $(P):$(R):CURRENT_SP
    - STATE_RB   (RO): $(P):$(R):STATE_RB
    - STATE_SP   (RW): $(P):$(R):STATE_SP

    Expected state values (string enums): OFF, ON, STANDBY, FAULT, RESET
    Note: Internally FAULT is mapped to ophyd_ps_state.ERROR.
    """

    # PV layout
    current_rb = Cpt(EpicsSignalRO, ":CURRENT_RB")  # float readback
    current = Cpt(EpicsSignal, ":CURRENT_SP")       # float setpoint
    state_rb = Cpt(EpicsSignalRO, ":STATE_RB")      # string/enum readback
    state = Cpt(EpicsSignal, ":STATE_SP")           # string/enum setpoint

    def __init__(
        self,
        name: str,
        prefix: str,
        max: float = 10.0,
        min: float = -10.0,
        verbose: int = 0,
        **kwargs,
    ):
        # Initialize common PS base (limits, bookkeeping)
        OphydPS.__init__(self, name=name, min_current=min, max_current=max, verbose=verbose, **kwargs)
        if read_attrs is None:
            read_attrs = ['current_rb', 'state_rb']
        # Initialize ophyd Device with this prefix
        epik8sDevice.__init__(
            self,
            prefix,
            read_attrs=read_attrs,
            configuration_attrs=None,
            name=name,
            parent=None,
            **kwargs,
        )

        # Internal cached values
        self._current = None
        self._setpoint = None
        self._state: ophyd_ps_state = ophyd_ps_state.UKNOWN

        # Subscriptions to keep cache in sync
        # self.current_rb.subscribe(self._on_current_change_rb)
        # self.state_rb.subscribe(self._on_state_change_rb)

        # Prime initial values (if connected)
        try:
            self._current = self.current_rb.get()
        except Exception:
            self._current = None
        try:
            raw_state = self.state_rb.get()
            self._state = self._decode_state(raw_state)
        except Exception:
            self._state = ophyd_ps_state.UKNOWN
        try:
            self._setpoint = self.current.get()
        except Exception:
            self._setpoint = None

    # ----------------------
    # Callbacks / subscriptions
    # ----------------------
    def _on_current_change_rb(self, pvname=None, value=None, **kwargs):
        self._current = value
        self.on_current_change(self._current, self)

    def _on_state_change_rb(self, pvname=None, value=None, **kwargs):
        self._state = self._decode_state(value)
        self.on_state_change(self._state, self)

    # ----------------------
    # Public API overrides
    # ----------------------
    def set_current(self, value: float):
        """Set the magnet current via CURRENT_SP, respecting min/max limits."""
        super().set_current(value)
        self._setpoint = value
        # Put to hardware; leave ramping/slewing to underlying IOC
        self.current.put(value)

    def set_state(self, state: Union[ophyd_ps_state, str]):
        """Set the magnet state via STATE_SP.

        Accepts either ophyd_ps_state or a string (OFF, ON, STANDBY, FAULT, RESET).
        """
        st_enum = self._to_enum(state)
        # Persist intent; IOC may take time to reflect it in STATE_RB.
        self.last_state_set = st_enum
        self.state.put(self._encode_state(st_enum))

    def get_current(self) -> float:
        return self.current_rb.get()

    def get_state(self) -> ophyd_ps_state:
        return self.state_rb.get()

    # ----------------------
    # Helpers for state encoding/decoding
    # ----------------------
    def _to_enum(self, state: Union[ophyd_ps_state, str]) -> ophyd_ps_state:
        if isinstance(state, ophyd_ps_state):
            return state
        if isinstance(state, str):
            s = state.strip().upper()
            if s == "FAULT":
                return ophyd_ps_state.ERROR
            if s in ("ON", "OFF", "STANDBY", "RESET"):
                return ophyd_ps_state[s]
        # Fallback
        return ophyd_ps_state.UKNOWN

    def _encode_state(self, state: ophyd_ps_state) -> str:
        """Return the string to write to STATE_SP."""
        # Map our internal ERROR back to FAULT if writing would ever use it
        if state == ophyd_ps_state.ERROR:
            return "FAULT"
        return state.value

    def _decode_state(self, raw) -> ophyd_ps_state:
        """Map raw PV value (enum/int/str) to ophyd_ps_state."""
        # Ophyd typically returns strings for mbbi, so prefer string handling
        try:
            if isinstance(raw, str):
                s = raw.strip().upper()
                if s in ("OFF", "ON", "STANDBY", "RESET"):
                    return ophyd_ps_state[s]
                if s in ("FAULT", "ERROR"):
                    return ophyd_ps_state.ERROR
                if s == "INTERLOCK":
                    return ophyd_ps_state.INTERLOCK
            elif isinstance(raw, (int, float)):
                # Generic fallback mapping if IOC returns numeric states.
                # 0:OFF, 1:ON, 2:STANDBY, 3:FAULT, 4:RESET (heuristic)
                mapping = {
                    0: ophyd_ps_state.OFF,
                    1: ophyd_ps_state.ON,
                    2: ophyd_ps_state.STANDBY,
                    3: ophyd_ps_state.ERROR,  # treat FAULT as ERROR internally
                    4: ophyd_ps_state.RESET,
                }
                return mapping.get(int(raw), ophyd_ps_state.UKNOWN)
        except Exception:
            pass
        return ophyd_ps_state.UKNOWN

    # ----------------------
    # Convenience methods
    # ----------------------
    def on(self):
        self.set_state(ophyd_ps_state.ON)

    def off(self):
        self.set_state(ophyd_ps_state.OFF)

    def standby(self):
        self.set_state(ophyd_ps_state.STANDBY)

    def reset(self):
        self.set_state(ophyd_ps_state.RESET)
