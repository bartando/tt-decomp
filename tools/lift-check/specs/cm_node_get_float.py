"""Direct, virtual and disconnected ports; callback writes the returned scalar."""
from liftcheck.spec import *

FUNCTION = "rage::cmNode_GetFloat"
ADDRESS = 0x82179350
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1200
EXTERNS = {"rage::g_cm_zeroFloat": 0x8202D110}


def get_float(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 4, 4))


CALLS = {"node.vfn_4": model(get_float, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    port = t.alloc(8, "port")
    node = t.alloc(8, "node")
    direct = t.alloc(4, "direct")
    t.w32(node, t.vtable("node"))
    t.wf32(node + 4, r.uniform(-10000, 10000))
    t.wf32(direct, r.uniform(-10000, 10000))
    kind = r.choice((0, 1, 1, 2, 2, 3, 0xffffffff, t.u32()))
    t.w32(port, node if kind == 2 else direct)
    t.w32(port + 4, kind)
    t.args(r3=port)
