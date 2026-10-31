"""0x8244EFE8: add 60 to this and preserve r4 and the append return value."""
from liftcheck.spec import *

FUNCTION = "msgMsgSink_vfn_42_EFE8_1"
ADDRESS = 0x8244EFE8
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000
CALLS = {"rage_C1A8": stub(args=("r3", "r4"), auto_out=False)}


def inputs(t):
    t.args(r3=t.alloc(0x200, "owner"), r4=t.alloc(16, "value"))
