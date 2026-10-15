"""msgMsgSink_8B90_g (0x82448B90): null-guard +0x7C, tail-call msgMsgSink_D1D8_sp with r4."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink_8B90_g"
ADDRESS = 0x82448B90
SOURCE = "src/game/network/xact_sink_forwards.cpp"

CALLS = {"msgMsgSink_D1D8_sp": stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    rng = t.rng
    sink = t.alloc(0x80, "sink")
    t.w32(sink + 0x7C, 0 if rng.random() < 0.3 else t.alloc(16, "chain"))
    t.args(r3=sink, r4=rng.randrange(0x10000))
