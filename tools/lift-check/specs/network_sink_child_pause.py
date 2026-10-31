from specs._network_sink_children_cases import *
FUNCTION='msgChild_SetPaused'
ADDRESS=0x82459D70
def inputs(t): t.args(r3=make_child(t),r4=t.u32())
