"""pongNetMessageHolder_2228_2h (0x82582228): push the static node 0x825D1960
onto the holder singleton's list (+8) and increment its count (+0xC)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongNetMessageHolder_2228_2h"
ADDRESS = 0x82582228
SOURCE = "src/game/network/pong_network.cpp"
NODE = 0x825D1960
RET = None

HOLDER = {}
CALLS = {"pongNetMessageHolder_FAE0_isl": model(lambda ctx: ctx.ret(r3=HOLDER["a"]))}


def inputs(t):
    HOLDER["a"] = t.alloc(0x10, "holder")
    t.w32(NODE + 8, t.rng.randrange(1 << 32))
    t.args()
