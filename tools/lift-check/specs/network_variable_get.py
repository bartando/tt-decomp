from specs._network_wave_acquire_cases import *
FUNCTION='msgMsgSink::GetPropertyLocked'
ADDRESS=0x8244F330
def inputs(t):
    target=cue(t)
    out=t.alloc(4,'variable value')
    t.args(r3=target,r4=t.rng.choice([0,1,2,3,0xFFFF0001,0xFFFF0002,t.u32()]),r5=out)
