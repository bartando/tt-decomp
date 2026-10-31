from specs._network_wave_acquire_cases import *
FUNCTION='msgMsgSink::SetPropertyLocked'
ADDRESS=0x8244F268
def inputs(t):
    t.args(r3=cue(t),r4=t.u32(),f1=t.rng.choice([0.0,1.0,-1.0,0.5,float('nan')]))
