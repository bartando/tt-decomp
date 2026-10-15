"""gmBallNode::SetScale (0x82282318): drawn scale, sphere radius, optional write-back."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::SetScale"
ADDRESS = 0x82282318
SOURCE = "src/game/ball/pong_ball.cpp"

# The declaration spans two lines, so its marker isn't picked up.
EXTERNS = {"RTDynamicCast": 0x82430978}


def _cast(ctx):
    return ctx.r(3) if ctx.rng.random() < 0.7 else 0


CALLS = {
    0x82430978: stub(ret=_cast),          # RTDynamicCast: the bound or null
    "bound.vfn_37": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    draw = t.alloc(0x80, "drawInst")
    inst = t.alloc(0x10, "inst")
    arch = t.alloc(0x20, "arch")
    bound = t.alloc(0x80, "bound")
    t.w32(node + 0x7C, draw)
    t.w32(node + 0x74, inst)
    t.w32(inst + 4, arch)
    t.w32(arch + 0xC, bound)
    t.w32(bound, t.vtable("bound", 40))
    t.w8(node + 0x88, rng.choice([0, 1, 0x80]))
    t.args(r3=node, f1=rng.uniform(0.05, 10.0))
