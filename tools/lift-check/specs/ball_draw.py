"""gmBallNode::Draw (0x82281C10): draws the ball, the first trail, and queues the shadow,
spin texture and splash."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::Draw"
ADDRESS = 0x82281C10
SOURCE = "src/game/ball/pong_ball.cpp"

CALLS = {
    "draw.vfn_1": stub(ret="void"),
    "trail.vfn_1": stub(ret="void"),
    "spin.vfn_1": stub(ret="void"),
    0x822278D8: stub(ret="void"),        # pongDrawBucket_AddEntry
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    draw = t.alloc(0x80, "drawInst")
    t.w32(draw, t.vtable("draw"))
    t.w32(draw + 0x60, rng.choice([0, t.u32()]))
    t.w32(node + 0x7C, draw)

    def obj(off, name, size=0x20, vt=True):
        if rng.random() < 0.7:
            p = t.alloc(size, name)
            if vt:
                t.w32(p, t.vtable(name))
            t.w32(node + off, p)
        else:
            t.w32(node + off, 0)

    obj(0xAC, "trail")
    obj(0xB4, "shadow", vt=False)
    obj(0xB8, "spin")
    obj(0xBC, "splash", vt=False)
    bucket = t.alloc(0x60, "bucket")
    t.w32(0x826064F4, bucket)
    t.args(r3=node)
