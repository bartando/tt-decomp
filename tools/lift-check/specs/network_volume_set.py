from specs._network_volume_cases import *
FUNCTION='rage::xactSink_SetVolume'
ADDRESS=0x82454020
def inputs(t): t.args(r3=make_list(t),f1=t.rng.choice([scale(t),float('nan'),float('inf'),-float('inf')]))
