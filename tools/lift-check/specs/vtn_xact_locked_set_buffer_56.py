"""msgMsgSink::vfn_56 (0x82456E38): under the critical section at (+0x38)+0x90,
call slot 34 (SetMessageBuffer) with r4, then 3E68 on +0x188/+0x18C with
this+0x148; returns slot 34's result."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink::vfn_56"
ADDRESS = 0x82456E38
SOURCE = "src/game/network/msg_msg_sink.cpp"
INNER = "msgMsgSink_vfn_34"
NOTIFY = "msgMsgSink_3E68_g"

CALLS = {
    0x82585E0C: stub(ret="void", args=("r3",)),
    0x82585DFC: stub(ret="void", args=("r3",)),
    INNER: stub(args=("r3", "r4"), deref={"r4": 0}),
    NOTIFY: stub(ret="void", args=("r3", "r4"), deref={"r4": 0}),
}


def inputs(t):
    obj = t.alloc(0x1A0, "sink")
    t.w32(obj + 0x38, t.alloc(0xA0, "engine"))
    for off in (0x188, 0x18C):
        t.w32(obj + off, 0 if t.rng.random() < 0.3 else t.alloc(0x30, f"sub{off:x}"))
    t.args(r3=obj, r4=t.alloc(8, "param"))
