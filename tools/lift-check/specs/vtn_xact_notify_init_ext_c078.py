"""msgMsgSink::InitializeExtended (0x8245C078): A970 with r4..r7 passed through,
then vtables 0x820054E8/0x82003E28, keep the low 5 bits of +0xD4, clear
+0x44..+0x60 and 22 words from +0x70; returns this."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink::InitializeExtended"
ADDRESS = 0x8245C078
SOURCE = "src/game/network/msg_msg_sink.cpp"

CALLS = {"msgMsgSink_A970_2h": stub(args=("r3", "r4", "r5", "r6", "r7"))}


def inputs(t):
    obj = t.alloc(0xD8, "sink")
    t.args(r3=obj, r4=t.rng.randrange(1 << 32), r5=t.alloc(8, "bucket"),
           r6=t.rng.randrange(0x10000), r7=t.rng.randrange(1 << 32))
