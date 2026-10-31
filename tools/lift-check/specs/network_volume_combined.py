from specs._network_volume_cases import *
FUNCTION='rage::xactSink_GetCombinedVolume'
ADDRESS=0x82454AC0
def inputs(t): t.args(r3=make_root(t))
