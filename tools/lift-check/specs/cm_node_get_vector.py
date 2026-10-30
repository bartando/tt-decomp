"""0x821792D8: bit-exact direct copy, virtual slot 2, and disconnected zero.

Vectors obey the function's 16-byte alignment contract. Random payload bytes
include NaNs, signed zeros, and noncanonical values; this is a copy, not math.
"""
from liftcheck.spec import *

FUNCTION = "rage::cmNode_GetVector"
ADDRESS = 0x821792D8
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1200


def get_vector(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 16, 16))
    # GetVector's return register is unspecified; the wrapper must return dst.
    ctx.ret(r3=0x13579bdf)


CALLS = {"node.vfn_2": model(get_vector, args=("r3", "r4"))}


def inputs(t):
    port = t.alloc(8, "port")
    node = t.alloc(48, "node")
    direct = t.alloc(48, "direct_with_guards") + 16
    dst = t.alloc(48, "output_with_guards") + 16
    t.w32(node, t.vtable("node"))
    if t.rng.randrange(2) == 0:
        # Deliberately include bit patterns random bytes rarely reach.
        special = (0, 0x80000000, 1, 0x80000001, 0x007fffff,
                   0x7f800000, 0xff800000, 0x7fc12345, 0x7f812345)
        for source in (direct, node + 16):
            for lane in range(4):
                t.w32(source + lane * 4, t.rng.choice(special))
    kind = t.rng.choice((0, 1, 1, 2, 2, 3, 0xffffffff, 0x80000000, t.u32()))
    if kind == 1 and t.rng.randrange(4) == 0:
        dst = direct  # Identical source and destination is a valid direct copy.
    t.w32(port, node if kind == 2 else direct)
    t.w32(port + 4, kind)
    t.args(r3=dst, r4=port)
