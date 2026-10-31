from specs._network_sink_deadline_cases import *
FUNCTION = 'msgSink_GetDeadlineOverrun'
ADDRESS = 0x824564D8
SOURCE = 'src/game/network/msg_sink_timing.cpp'
TRIALS = 600
def inputs(t): t.args(r3=make_sink(t))
