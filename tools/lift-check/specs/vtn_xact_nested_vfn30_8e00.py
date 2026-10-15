"""msgMsgSink_8E00_sp (0x82458E00): if +0x24 is set, tail-call its vtable
slot 30 with r4 unchanged."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink_8E00_sp"
ADDRESS = 0x82458E00
SOURCE = "src/game/network/msg_msg_sink.cpp"
RET = None
SLOT = 30

CALLS = {f"nested.vfn_{SLOT}": stub(ret="void", args=("r3", "r4"), deref={"r4": 0})}


def inputs(t):
    obj = t.alloc(0x30, "obj")
    if t.rng.random() < 0.3:
        t.w32(obj + 0x24, 0)
    else:
        nested = t.alloc(0x10, "nested")
        t.w32(nested, t.vtable("nested", 32))
        t.w32(obj + 0x24, nested)
    t.args(r3=obj, r4=t.alloc(8, "arg"))
