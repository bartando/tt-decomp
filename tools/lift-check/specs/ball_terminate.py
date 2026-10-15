"""gmBallNode::Terminate (0x82281368): unpublish the ball, free the effects."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::Terminate"
ADDRESS = 0x82281368
SOURCE = "src/game/ball/pong_ball.cpp"

CALLS = {
    0x820C00C0: stub(ret="void"),                       # rage_free
    "spinSink.vfn_0": stub(ret="void", args=("r3", "r4")),
    "splash.vfn_0": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    for off in (0xAC, 0xB0, 0xB4):
        t.w32(node + off, rng.choice([0, t.u32()]))
    if rng.random() < 0.7:
        spin = t.alloc(0x20, "spinTex")
        t.w32(spin + 0x10, t.vtable("spinSink"))
        t.w32(node + 0xB8, spin)
    else:
        t.w32(node + 0xB8, 0)
    if rng.random() < 0.7:
        splash = t.alloc(0x10, "splash")
        t.w32(splash, t.vtable("splash"))
        t.w32(node + 0xBC, splash)
    else:
        t.w32(node + 0xBC, 0)
    slot = t.alloc(4, "ballInstSlot")
    t.w32(0x8271A2F4, slot)
    t.args(r3=node)
