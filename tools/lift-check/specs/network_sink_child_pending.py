from specs._network_sink_children_cases import *
FUNCTION='msgChild_HasPendingTarget'
ADDRESS=0x82459D58
def inputs(t): t.args(r3=make_child(t))
