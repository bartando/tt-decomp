from specs._network_wave_acquire_cases import *
FUNCTION='xactBank_GetWaveRecord'
ADDRESS=0x82448C60
def inputs(t): t.args(r3=owner(t,False),r4=(t.u32()&0xFFFF0000)|t.rng.randrange(12))
