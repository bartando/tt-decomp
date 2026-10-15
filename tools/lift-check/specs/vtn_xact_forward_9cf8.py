"""game_9CF8_h (0x82459CF8): if +0x18 is set, tail-call msgMsgSink_8DE0_sp on
it with r4 unchanged."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "game_9CF8_h"
ADDRESS = 0x82459CF8
SOURCE = "src/game/network/msg_msg_sink.cpp"
RET = None

CALLS = {"msgMsgSink_8DE0_sp": stub(ret="void", args=("r3", "r4"), deref={"r4": 0})}


def inputs(t):
    obj = t.alloc(0x20, "obj")
    t.w32(obj + 0x18, 0 if t.rng.random() < 0.3 else t.alloc(0x30, "inner"))
    t.args(r3=obj, r4=t.alloc(8, "arg"))
