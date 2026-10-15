"""sgPhysicalObject::Transform (0x823D9208), slot 29: cull test + draw-bucket submit."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "sgPhysicalObject::Transform"
ADDRESS = 0x823D9208
SOURCE = "src/scene/sg_physical.cpp"

EXTERNS = {"g_rendererState": 0x8260641C, "g_drawBucket": 0x826064F4}


def _vis_test(ctx):
    ctx.write(ctx.r(6), bytes([ctx.rng.randrange(256)]))
    ctx.write(ctx.r(7), ctx.rng.randbytes(4))
    return ctx.rng.choice([0, 1, 7])


CALLS = {
    "draw.vfn_9": stub(ret=_vis_test, args=("r3", "r4", "r5")),
    "draw.vfn_10": stub(),
    "entry.vfn_1": stub(ret="void"),
    "pongDrawBucket_AddEntry": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x80, "node")
    t.w32(node + 0x60, t.vtable("entry", slots=8))
    t.w8(node + 0x70, rng.choice([0, 0, 1]))
    obj = t.alloc(0x90, "drawObj")
    t.w32(node + 0x7C, obj)
    drawable = t.alloc(0x10, "drawable")
    t.w32(drawable, t.vtable("draw", slots=12))
    t.w32(obj + 0x60, drawable if rng.random() < 0.9 else 0)
    t.w32(obj + 0x14, t.alloc(0x60, "data"))
    t.w32(obj + 0x68, t.alloc(0x40, "xformSrc") if rng.random() < 0.4 else 0)
    if rng.random() < 0.3:
        frames = t.alloc(0x20, "frames")
        t.w32(frames + 0x14, t.alloc(0x100, "frameBuf"))
        state = t.alloc(0x50, "state")
        t.w32(state + 0x40, frames)
        t.w32(state + 0x44, rng.randrange(0, 4))
        coll = t.alloc(0x10, "collider")
        t.w32(coll + 0x0C, state)
        t.w32(obj + 0x6C, coll)
    else:
        t.w32(obj + 0x6C, 0)
    view = t.alloc(0xA0, "view")
    viewer = t.alloc(0x30, "viewer")
    t.w32(viewer + 0x2C, view)
    world = t.alloc(0x30, "world")
    t.w32(world + 0x28, viewer)
    t.w32(0x8260641C, world)
    t.args(r3=node)
