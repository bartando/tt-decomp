from specs._network_wave_acquire_cases import *
FUNCTION='msgMsgSink_8D10_g'
ADDRESS=0x82448D10
def inputs(t): t.args(r3=owner(t),r4=(t.u32()&0xFFFF0000)|t.rng.randrange(12))
