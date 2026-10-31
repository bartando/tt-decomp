"""0x824514E8: add 20 to this, forward r4, and return the appended node."""
from liftcheck.spec import *

FUNCTION = "msgMsgSink::ForwardToRageHandler"
ADDRESS = 0x824514E8
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000
CALLS = {"rage_C1A8": stub(args=("r3", "r4"), auto_out=False)}


def inputs(t):
    t.args(r3=t.alloc(0x200, "owner"), r4=t.alloc(16, "value"))
