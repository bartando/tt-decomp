"""0x822621B0: general CM port byte reader, not a conditional-node method.

Compare raw r3, calls, and all writes. Direct/virtual bytes include values other
than 0/1: the original lbz preserves them. Invalid tags must not dereference data.
"""
from liftcheck.spec import *

FUNCTION = "cmPort_GetBool"
ADDRESS = 0x822621B0
SOURCE = "src/game/misc/cm_operators.cpp"
TRIALS = 1200
RET = "r3"


def get_bool(ctx):
    # Write exactly one out-byte; poison bytes around it remain untouched.
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 4, 1))


CALLS = {"node.vfn_3": model(get_bool, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    port = t.alloc(16, "portAndGuard")
    direct = t.alloc(16, "directAndGuard")
    node = t.alloc(16, "nodeAndGuard")
    t.w32(node, t.vtable("node"))
    values = (0, 1, 2, 0x7f, 0x80, 0xfe, 0xff, r.randrange(256))
    t.w8(direct, r.choice(values))
    t.w8(node + 4, r.choice(values))
    kind = r.choice((1, 1, 2, 2, 0, 3, 0x101, 0x102, 0xffffffff, t.u32()))
    t.w32(port, node if kind == 2 else direct if kind == 1 else r.choice((0, 0xdeadbeef)))
    t.w32(port + 4, kind)
    t.args(r3=port)
