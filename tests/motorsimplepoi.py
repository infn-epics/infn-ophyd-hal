from infn_ophyd_hal import OphydTmlMotor
import logging
# elem_name 	Zone 	yag_step 	calibration_step 	Perm_Q_step 	Capillar_step
# AC1FLG01 	LINAC 	670000 	550000 	
	
# AC2FLG01 	LINAC 	3120000 	2800000 	
	
# AC3FLG01 	LINAC 	2275560 	1575560 	
	
# CMBEOS01 	COMB 	4968360 	4407960 	850000 	1950000
# CMBPLV01 	COMB 	212000 	332000 	
# 	480000
# CMBPQV01 	COMB 	
# 	0 	561380 	
# CMBPQV02 	COMB 	400000 	200320 	
	
# CMBTHV01 	COMB 	1470000 	1325000 	
	
# GUNFLG01 	LINAC 	688640 	688640 	
	
# UTLFLG01 	LINAC 	3000000 	2500000 	
	
# UTLFLG02 	LINAC 	1190000 	992160
# # Example usage
logging.basicConfig(level=logging.INFO)
def myreadupdate(timestamp=None, value=None, **kwargs):
    print(f" read {value}")
    
motor = OphydTmlMotor("SPARC:TML:CH1:AC1FLG01",name="AC1FLG01", poi=[{"name": "yag", "pos": 670000}, {"name": "calibration", "pos": 550000}])
motor.user_readback.subscribe(myreadupdate)

print(str(motor.get_pos(True)))

logging.info("Homing")
motor.home(1,wait=True)
for p in ["yag","calibration"]:
    logging.info(f"Moving {p}")

    motor.move(p,True)

    pos=motor.get_pos(True)
    
    if pos['name'] == p:
        logging.info(f"position reached {p}: {pos['pos']}")
    else:
        logging.warning(f"position NOT reached {p}: {pos['pos']}")


    
# Perform motor actions
# motor.home()
# motor.set(100)