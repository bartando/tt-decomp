from specs._network_sink_deadline_cases import *
FUNCTION = 'msgMsgSink::DispatchVirtualMethod'
ADDRESS = 0x824542D0
SOURCE = 'src/game/network/msg_sink_timing.cpp'
TRIALS = 400
def inputs(t): t.args(r3=make_peer(t),r4=t.u32())
