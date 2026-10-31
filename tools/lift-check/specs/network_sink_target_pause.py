from specs._network_sink_children_cases import *
FUNCTION='msgMsgSink_8E88_sp'
ADDRESS=0x82458E88
def inputs(t): t.args(r3=make_inner(t),r4=t.u32())
