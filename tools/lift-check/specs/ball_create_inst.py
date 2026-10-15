"""gmBallNode::CreateInst (0x82282430): new pongBallInstance (0xD0 bytes)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::CreateInst"
ADDRESS = 0x82282430
SOURCE = "src/game/ball/pong_ball.cpp"

SDA = 0x82600000


def _maybe_alloc(ctx):
    return ctx.alloc(ctx.r(4)) if ctx.rng.random() < 0.8 else 0


CALLS = {
    0x820C0038: stub(ret="void"),
    "alloc.vfn_1": stub(ret=_maybe_alloc, args=("r3", "r4", "r5")),
    0x8227F870: stub(),                    # pongBallInstance ctor
}


def inputs(t):
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    sda = t.alloc(0x10, "sda", fill="zero")
    tls = t.alloc(0x10, "tls", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(sda, tls)
    t.w32(tls + 4, allocator)
    t.w32(allocator, t.vtable("alloc"))
    t.w32(SDA, sda)
    t.args(r3=node, r13=sda)
