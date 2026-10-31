from specs._network_sink_deadline_cases import *
FUNCTION = 'msgMsgSink::vfn_66'
ADDRESS = 0x82456920
SOURCE = 'src/game/network/msg_sink_timing.cpp'
TRIALS = 400
def inputs(t): t.args(r3=make_sink(t),r4=make_peer(t))
