"""phUpdateObject::AddToRenderBucket (0x8227D768), slot 4."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "phUpdateObject::AddToRenderBucket"
ADDRESS = 0x8227D768
SOURCE = "src/physics/ph_update_object.cpp"

def _vis_test(ctx):
    ctx.write(ctx.r(6), bytes([ctx.rng.randrange(256)]))
    ctx.write(ctx.r(7), ctx.rng.randbytes(4))
    return ctx.rng.choice([0, 1, 7])


CALLS = {
    # visibility test: (drawable, transform, view+0x98 word, &visible, &lodParam)
    "draw.vfn_9": stub(ret=_vis_test, args=("r3", "r4", "r5")),
    "draw.vfn_10": stub(),
    "obj.vfn_1": stub(ret="void"),
    "pongDrawBucket_AddEntry": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x90, "obj")
    t.w32(obj, t.vtable("obj", slots=9))
    drawable = t.alloc(0x10, "drawable")
    t.w32(drawable, t.vtable("draw", slots=12))
    t.w32(obj + 0x60, drawable if rng.random() < 0.9 else 0)
    data = t.alloc(0x60, "data")
    t.w32(obj + 0x14, data)
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
    t.args(r3=obj, r4=rng.choice([0, 1]))  # an MSVC bool: only the low byte is tested
