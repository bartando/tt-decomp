from specs._network_volume_cases import *
FUNCTION='rage::xactGroup_GetVolume'
ADDRESS=0x82448AB8
def inputs(t): t.args(r3=make_group(t),r4=(t.u32()&0xFFFF0000)|t.rng.randrange(8))
