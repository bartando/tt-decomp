from liftcheck.spec import *

FUNCTION = "msgMsgSink_84C0_gen"
ADDRESS = 0x824484C0
SOURCE = "src/game/network/pong_network_io.cpp"
TRIALS = 1000
CALLS = {"xe_GetCurrentThreadId": stub(ret=lambda ctx: _current)}
_current = 0


def inputs(t):
    global _current
    obj = t.alloc(0x18, "sink")
    _current = t.rng.choice((0, 1, 0xffffffff, t.u32()))
    t.w32(obj + 0x14, t.rng.choice((_current, 0, 1, 0xffffffff, t.u32())))
    t.args(r3=obj)
