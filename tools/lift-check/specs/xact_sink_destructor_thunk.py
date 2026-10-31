"""0x82456130: adjust this by -8, retaining the deleting destructor's flags."""
from liftcheck.spec import *

FUNCTION = "msgMsgSink_vfn_23_6130_1"
ADDRESS = 0x82456130
SOURCE = "src/game/network/msg_msg_sink.cpp"
TRIALS = 1000
CALLS = {"msgMsgSink_6220_w": stub(ret="void", args=("r3", "r4"), auto_out=False)}


def inputs(t):
    t.args(r3=t.alloc(0x200, "sink") + 8, r4=t.u32())
