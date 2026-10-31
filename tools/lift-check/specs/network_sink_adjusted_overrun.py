"""0x82456550: disabled deadline bypass, wrapped context-time adjustment."""
from specs._network_sink_deadline_cases import *
FUNCTION='msgSink_GetAdjustedDeadlineOverrun'
ADDRESS=0x82456550
SOURCE='src/game/network/msg_sink_timing.cpp'
TRIALS=600
def inputs(t):
    sink=make_sink(t)
    context=t.alloc(64,'context')
    t.w32(sink+0x38,context)
    t.w32(context+0x28,t.rng.choice([0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()]))
    t.args(r3=sink)
