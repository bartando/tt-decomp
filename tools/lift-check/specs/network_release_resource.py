"""0x82353258: resource, data word at +12 and zero auxiliary to shared C API."""
from liftcheck.spec import *
FUNCTION='msgMsgSink_3258_wrh'
ADDRESS=0x82353258
SOURCE='src/game/network/msg_msg_sink.cpp'
TRIALS=400
CALLS={'grc_2CC8':stub(ret='void',args=('r3','r4','r5'))}
def inputs(t):
    holder=t.alloc(32,'holder')
    t.w32(holder+12,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.args(r3=holder)
