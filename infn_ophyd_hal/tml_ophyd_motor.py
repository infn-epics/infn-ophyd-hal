from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, PositionerBase
from ophyd.status import MoveStatus, Status
from .epik8s_device import epik8sDevice

import logging, time
logger = logging.getLogger(__name__)
# Constants for motor commands and states
MAX_RETRIES=3
RETRY_DELAY=2

NOSTATE = -1
PROCESSING = 4
ERROR = 6
FAULT = 8
HOMED = 0x4000
MOVING = 0x0200
CMD_HOME = 3
CMD_ABS_POS = 2
CMD_REL_POS = 1
CMD_JOGF = 4
CMD_JOGR = 5
CMD_NONE = 0


RUN = 1
STOP = 2
POS_TOLERANCE = 10

class OphydTmlMotor(epik8sDevice, PositionerBase):
    
    mot_msta = Cpt(EpicsSignalRO, ":MSTA")
    mot_stat = Cpt(EpicsSignalRO, ":STAT")
    user_readback = Cpt(EpicsSignalRO, ":RBV")
    mot_msgs = Cpt(EpicsSignal, ":MSGS")
    mot_act_sp = Cpt(EpicsSignal, ":ACT")
    mot_act_rb = Cpt(EpicsSignal, ":ACT_RB")
    mot_actx_sp = Cpt(EpicsSignal, ":ACTX_SP")
    user_setpoint = Cpt(EpicsSignal, ":VAL_SP")
    mot_val_rb = Cpt(EpicsSignal, ":VAL_RB")
    motor_moving= Cpt(EpicsSignalRO, ":MSTA.BA")
    motor_done_move= Cpt(EpicsSignalRO, ":MSTA.B1")
    velocity = Cpt(EpicsSignal, ':VELO_SP')
    acceleration = Cpt(EpicsSignal, ':ACCL_SP')
    home_velocity = Cpt(EpicsSignal, ':HVEL_SP')
    home_acceleration = Cpt(EpicsSignal, ':VAL_SP')
    jog_velocity = Cpt(EpicsSignal, ':JVEL_SP')
    jog_acceleration = Cpt(EpicsSignal, ':JAR_SP')
    
    direction_of_travel=Cpt(EpicsSignalRO, ':MSTA.B1')
    high_limit_switch = Cpt(EpicsSignalRO, ':MSTA.B2')
    low_limit_switch = Cpt(EpicsSignalRO, ':MSTA.BD')
    homed            =  Cpt(EpicsSignalRO, ':MSTA.BE')
    
    
    def __init__(self, prefix, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None,poi=None, **kwargs):
        
        if read_attrs is None:
            read_attrs = ['user_readback', 'user_setpoint']
            
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
        self.poi = poi
        self.user_readback.name = self.name
        # self.mot_stat.subscribe(self._on_mot_stat_change)
        self.user_readback.subscribe(self._on_user_readback_change)
        self.mot_msta.subscribe(self._on_mot_msta_change)

        # Initial connection check
        self.mot_stat_value = self.mot_stat.get()
        self.mot_msta_value = self.mot_msta.get()
        #logging.debug(f"{name} State:\n{self.decode()}")
        # self.enable()
        
    def stage(self):
        logging.info(f"{self.name} State:\n{self.decode()}")

        super().stage()

    def unstage(self):
        logging.info(f"{self.name} Unstage\n")

        
        super().unstage()
        
    def __del__(self):
        '''Destructor to handle any necessary cleanup.'''
        logger.debug(f"Cleaning up {self.name}")
        # self.mot_stat.unsubscribe(self._on_mot_stat_change)
        self.user_readback.unsubscribe(self._on_user_readback_change)
        self.mot_msta.unsubscribe(self._on_mot_msta_change)
        
        self.unstage()
        # Add any other necessary cleanup here
              
    def enable(self,restart=False):
        '''Check and Enable motor
        
            Parameters
            ----------
            restart
                Force stop and start
        
        '''
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if restart:
                    self.stop()
                    self.mot_msgs.put("STOP")
                    time.sleep(2) 
                    self.mot_msgs.put("START")
                    time.sleep(2)
                self.mot_stat_value = self.mot_stat.get()
                if self.mot_stat_value != "PROCESSING":
                    self.mot_msgs.put("STOP")
                    time.sleep(2) 
                    self.mot_msgs.put("START")
                return
            except Exception as e:
                logger.warning(f"ENABLE Attempt {attempt} failed with error: {e}")
                if attempt < MAX_RETRIES:
                    self.stop()

                    self.mot_msgs.put("STOP")

                    time.sleep(RETRY_DELAY) 
                    self.mot_msgs.put("START")
                else:
                    raise  # Reraise the last exception if all retries failed
            

        
                    


    def decode(self):
        status = ""
        if self.iserror():
            status += "- ERROR\n"
        if self.ishomed():
            status += "- homed\n"
        if self.limit() == 1:
            status += "- lsp\n"
        if self.limit() == -1:
            status += "- lsn\n"
        if self.limit() == -1000:
            status += "- lsp+lsn ERROR\n"
        status += "- dir " + str(self.dir()) + "\n"
        pos = self.user_readback.get()
        status += "- pos " + str(pos) + "\n"
        return status

    def iserror(self):
        return (self.mot_msta.get() & (1 << 0x9)) != 0

    def ishomed(self):
        return (self.mot_msta.get() & (1 << 0xE)) != 0

    def limit(self):
        lsn = self.mot_msta.get() & (1 << 0xD)
        lsp = self.mot_msta.get() & (1 << 2)
        if lsn:
            return -1
        if lsp:
            return 1
        if lsn and lsp:
            return -1000
        return 0
    
    def dir(self):
        return self.mot_msta.get() & 0x1
    
    def moving(self):
        '''Whether or not the motor is moving

        Returns
        -------
        moving : bool
        '''
        return (self.mot_msta.get() & (1 << 0xA)) != 0
    def home(self, direction, wait=True,timeout=120, **kwargs):
        
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"home")

                self.mot_act_sp.put(CMD_HOME)
                time.sleep(1)
                self.mot_actx_sp.put(RUN)
                stat = self.wait_homed(timeout)
                return stat
            except Exception as e:
                logger.warning(f"HOME Attempt {attempt} failed with error: {e}")
                self.stop()

                if attempt < MAX_RETRIES:
                    self.mot_msgs.put("STOP")

                    time.sleep(RETRY_DELAY) 
                    self.mot_msgs.put("START")

                else:
                    raise  # Reraise the last exception if all retries failed

        
    def stop(self):
        logger.debug(f"stop")

        self.mot_actx_sp.put(STOP)

    def egu(self):
        return "ustep"
    
    def move(self, position, wait=True,timeout=120, **kwargs):
        '''Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.

        Returns
        -------
        status : MoveStatus

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        ValueError
            On invalid positions
        RuntimeError
            If motion fails other than timing out
        '''
        if isinstance(position, str):
            posstr=position
            position = self.poi2pos(posstr)
            if(position<0):
                raise Exception("BAD POI "+posstr)
        if position == self.position():
            logging.info(f"already at {position}")
            return MoveStatus(self,position)
        
        self.check_value(position)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                stat=self.set(position,timeout)
                return stat
            except Exception as e:
                logger.warning(f"MOVE Attempt {attempt} failed with error: {e}")
                if attempt < MAX_RETRIES:
                    self.stop()
                    time.sleep(RETRY_DELAY) 

                    self.mot_msgs.put("STOP")
                    time.sleep(RETRY_DELAY) 
                    self.mot_msgs.put("START")

                else:
                    raise  # Reraise the last exception if all retries failed

        # Set the motor to the desired position
        return 
    
    def position(self):
        return self.user_readback.get()

    def set_current_position(self, pos):
        '''Configure the motor user position to the given value

        Parameters
        ----------
        pos
           Position to set.

        '''
        self.user_setpoint.put(pos)
  
    def set(self, position,wait=True,timeout=120):
        if isinstance(position, str):
            position = self.poi2pos(position)
        if (position == self.position()):
            logger.info(f"already in {position}")

            return MoveStatus(self,position)

        self.user_setpoint.put(position)
        time.sleep(0.5)

        self.mot_act_sp.put(CMD_ABS_POS)
        time.sleep(0.5)

        self.mot_actx_sp.put(RUN)
        logger.info(f"set {position}")
        time.sleep(5)
        if(self.motor_moving.get()):
            self.wait_move(timeout=240)
            return self.wait_done(wait,position,timeout)
        else:
            self.user_setpoint.put(0)
            self.mot_act_sp.put(CMD_NONE)


            raise Exception(f" motor not moving")

        # Set state to waitend or any other state needed

    def jogf(self,wait=True):
        self.mot_act_sp.put(CMD_JOGF)
        time.sleep(0.5)

        self.mot_actx_sp.put(RUN)
        # Set state to waitend or any other state needed
        logger.info(f"jogf")

        return self.wait_done(wait)

    def jogr(self,wait=True):
        self.mot_act_sp.put(CMD_JOGR)
        time.sleep(0.5)
        logger.info(f"jogr")

        self.mot_actx_sp.put(RUN)
        return self.wait_done(wait)

        # Set state to waitend or any other state needed

    def poi2pos(self, poi_name):
        if self.poi:
            for k in self.poi:
                if poi_name == k['name']:
                    return k['pos']
        return -1000

    def pos2poi(self, position):
        if self.poi:
            for k in self.poi:
                if k['pos'] - POS_TOLERANCE <= position <= k['pos'] + POS_TOLERANCE:
                    return k['name']
        return ""
    
    def set_rel(self, position, wait=True):
        self.user_setpoint.put(position)
        self.mot_act_sp.put(CMD_REL_POS)
        time.sleep(0.5)
        logger.info(f"set rel {position}")

        self.mot_actx_sp.put(RUN)
        return self.wait_done(wait)
            
    def _on_mot_stat_change(self, pvname=None, value=None, **kwargs):
        self.mot_stat_value = value
        logger.debug(f"[{self.name}] Mot stat changed: {value}")
        self._update()

    def _on_mot_msta_change(self, pvname=None, value=None, **kwargs):
        self.mot_msta_value = value
        logger.debug(f"[{self.name}] Mot msta changed: {value}")
        self._update()

    def _on_user_readback_change(self, pvname=None, value=None, **kwargs):
        self.current_position = value
        logger.debug(f"[{self.name}] Mot pos changed: {value}")
        self._update()
    
    def _update(self):
        logger.debug(f"State:\n{self.decode()}")
        return
    
    def get_pos(self,poi=False):
        pos=self.position()
        if poi:
            return {'pos':pos,"name":self.pos2poi(pos)}
        return pos
    
    def wait_done(self,wait=True,position=0,timeout=300):
        
        move_status = Status(self,timeout=timeout)
        
        
        # Define a callback to mark the status as done when the motor stops moving
        def done_moving(**kwargs):
            if self.motor_done_move.get():
                if not(move_status.done):
                    move_status.set_finished()
                self.motor_done_move.clear_sub(done_moving)

        # Subscribe to the motor moving signal
        self.motor_done_move.subscribe(done_moving)
        logger.debug(f"wait_done {timeout}")

        if wait:
            move_status.wait()
        logger.debug(f"exit wait_done {timeout}")

        return move_status
        
    def wait_move(self,wait=True,timeout=120):
        move_status = Status(self,timeout=timeout)
        
        
        # Define a callback to mark the status as done when the motor stops moving
        def start_moving(**kwargs):
            if self.motor_moving.get():
                if not(move_status.done):
                    move_status.set_finished()
                self.motor_moving.clear_sub(start_moving)

        # Subscribe to the motor moving signal
        self.motor_moving.subscribe(start_moving)
        logger.info(f"wait_move {timeout}")
        move_status.wait()
        logger.info(f"exit wait_move {timeout}")

        return move_status
    
    def wait_homed(self,wait=True,timeout=120):
        move_status = Status(self,timeout=timeout)
        
        
        # Define a callback to mark the status as done when the motor stops moving
        def start_moving(**kwargs):
            if self.homed.get():
                if not(move_status.done):
                    move_status.set_finished()
                self.homed.clear_sub(start_moving)

        # Subscribe to the motor moving signal
        self.homed.subscribe(start_moving)
        logger.info(f"wait_homed {timeout}")
        move_status.wait()
        logger.info(f"exit wait_homed {timeout}")

        return move_status