"""0x8244E978: preserve r4/r9 pointers and r6 index across the F518 lookup.

Covers null lookup, every header type, zero/in-range/out-of-range indices,
unaligned packed count/stride, default header offset, and full HRESULT return.
The lookup and E860 workers are call boundaries, with all meaningful arguments
compared. No tolerance or ignored writes.
"""
from liftcheck.spec import *

FUNCTION = "msgMsgSink::ProcessMessageWithIndex"
ADDRESS = 0x8244E978
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000
CALLS = {
    "msgMsgSink_F518_wrh": model(lambda c: c.ret(r3=c.r(3)), args=("r3",)),
    "msgMsgSink_E860_g": stub(ret=lambda c: c.rng.choice([0, 1, -1, -2147024809]),
        args=("r3", "r4", "r5", "r6"), deref={"r4": 8, "r5": 4}, auto_out=False),
}


def inputs(t):
    obj = t.alloc(0x200, "sink")
    message = t.alloc(20, "packedMessage")
    index = t.rng.choice([0, 1, 7, 65534, 65535])
    header = (t.u32() & ~31) | t.rng.choice([0, 1, 18, 18, 31])
    t.w32(message, header)
    count = t.rng.choice([0, index, min(index + 1, 65535), 65535])
    t.w32(message + 11, (count << 16) | t.rng.randrange(65536))
    t.w32(obj + 0x11C, t.rng.choice([0, message]))
    t.args(r3=obj, r4=t.alloc(8, "source"), r5=t.u32(), r6=index,
           r7=t.u32(), r8=t.u32(), r9=t.alloc(4, "outHandle"))
