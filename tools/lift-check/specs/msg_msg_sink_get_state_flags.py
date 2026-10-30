from liftcheck.spec import *

FUNCTION = "msgMsgSink::GetStateFlags"
ADDRESS = 0x8244DF58
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000

def inputs(t):
    obj = t.alloc(64, "sink")
    nested = t.alloc(96, "nested")
    t.w32(obj + 52, t.rng.choice([0, nested, nested, nested]))
    t.w32(nested + 80, t.rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 0xffffffff, t.u32()]))
    t.w8(nested + 52, t.rng.randrange(256))
    t.args(r3=obj)
