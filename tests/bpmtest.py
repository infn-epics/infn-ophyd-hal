from infn_ophyd_hal import SppOphydBpm
import logging

logging.basicConfig(level=logging.INFO)
def myreadupdate(timestamp=None, value=None, **kwargs):
    print(f" read {value}")


for i in ["AC1BPM01","AC2BPM01","AC3BPM01","PTLBPM01","PLXBPM01","PLXBPM02","UTLBPM01","PLXBPM03","PLXBPM04","DGLBPM01","DGLBPM02","DGLBPM03"]:
    bpm = SppOphydBpm(i,name=i)
    bpm.reset()## reset counter
    bpm.thsld(100)

    print(f"{i} cnt:{bpm.cnt.get()} thshld:{bpm.ths.get()} X:{bpm.x.get()} Y:{bpm.y.get()} VA:{bpm.va.get()} VB:{bpm.vb.get()} VC:{bpm.vc.get()} VD:{bpm.vd.get()} SUM:{bpm.sum.get()}")

    
# Perform motor actions
# motor.home()
# motor.set(100)