from specs._network_volume_cases import *
FUNCTION='rage::xactChild_UpdateVolume'
ADDRESS=0x82459C10
def inputs(t): t.args(r3=make_child(t))
