from liftcheck.spec import *

FUNCTION = "msgMsgSink::ProcessPendingMessages"
ADDRESS = 0x8244E050
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000
RET = None

CALLS = {
    "sink.vfn_16": model(lambda c: c.ret(r3=c.rng.choice([0, 8, 16, 24, 0xffffffff, 0x100])), args=("r3",)),
    "msgMsgSink_3B48_g": model(lambda c: c.ret(r3=c.rng.choice([0, 1, -1, 256])), args=("r3",)),
    "msgMsgSink_3DC8_g": stub(ret="void", args=("r3",)),
    "xactSound_Update": stub(ret="void", args=("r3",)),
}

def inputs(t):
    obj = t.alloc(64, "sink")
    message = t.alloc(64, "message")
    t.w32(obj, t.vtable("sink", 17))
    t.w32(obj + 52, t.rng.choice([0, message]))
    t.args(r3=obj)
