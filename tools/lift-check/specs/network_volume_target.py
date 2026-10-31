from specs._network_volume_cases import *
FUNCTION='rage::xactSink_SetTargetVolume'
ADDRESS=0x82458D80
def inputs(t): t.args(r3=make_inner(t),f1=scale(t))
