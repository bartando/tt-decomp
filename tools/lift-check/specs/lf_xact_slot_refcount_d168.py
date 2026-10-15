"""msgMsgSink_D168_sp (0x8244D168): walk the slot chain, +1 on each slot's count; slot 6 maps r4 to the next."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink_D168_sp"
ADDRESS = 0x8244D168
SOURCE = "src/game/network/msg_msg_sink.cpp"


# The slot is a u16 both ways (MSVC zero-extends), so inputs stay below 0x10000.
def _next(ctx):
    return ctx.rng.choice([0, 2, 5, 0xFFFF]) if ctx.rng.random() < 0.7 else 0xFFFF


CALLS = {"sink.vfn_6": stub(ret=_next, args=("r3", "r4"))}


def inputs(t):
    sink = t.alloc(0x70, "sink")
    t.w32(sink, t.vtable("sink"))
    t.w32(sink + 0x68, t.alloc(4 * 0x10000, "counts", fill="zero"))
    t.args(r3=sink, r4=t.rng.choice([0xFFFF, 0, 3, 0xFFFE]))
