"""0x8227D898: render cursor, untouched translation, scale and forwarded context."""
from liftcheck.spec import *

FUNCTION = "phUpdateObject::RenderShadow"
ADDRESS = 0x8227D898
SOURCE = "src/physics/ph_update_object.cpp"
TRIALS = 1000
CALLS = {"pongShadowMap_F010_g": stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r5": 64})}


def inputs(t):
    obj = t.alloc(0x90, "updateObject")
    drawable = t.alloc(16, "drawable")
    context = t.alloc(16, "context")
    frames = t.alloc(4 * 64, "frames")
    t.floats(frames, 64, -8, 8)
    for lane in range(16):
        if t.index % 5 == 0:
            t.wf32(frames + lane * 4, t.pick([1e-40, -1e-40, 0.0, -0.0]))
    index = t.index % 4
    t.w32(0x825C4898, index)
    t.w32(0x826065DC, (index + 1) % 4)
    t.w32(obj + 96, 0 if t.index % 7 == 0 else drawable)
    t.w32(obj + 128, frames)
    t.w32(0x826063C8, t.alloc(32, "shadowState"))
    scale = t.pick([0.0, -0.0, 1.0, -1.0, 1e-40, t.f32(-5, 5)])
    if t.index % 9 == 0:
        t.wf32(frames + index * 64, 1e-40)
        scale = 1e30
    elif t.index % 9 == 1:
        t.wf32(frames + index * 64, 1e-10)
        scale = 1e-30
    t.args(r3=obj, r4=context, f1=scale)
