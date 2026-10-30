"""0x8227D960: transform source selection, rollback cursor, four-lane scale."""
from liftcheck.spec import *

FUNCTION = "phUpdateObject::CommitTransform"
ADDRESS = 0x8227D960
SOURCE = "src/physics/ph_update_object.cpp"
TRIALS = 1000


def inputs(t):
    obj = t.alloc(0x90, "updateObject")
    data = t.alloc(80, "data")
    external = t.alloc(64, "externalTransform")
    frames = t.alloc(4 * 64, "frames")
    for p, n in [(data + 16, 16), (external, 16), (frames, 64), (obj + 112, 4)]:
        t.floats(p, n, -8, 8)
    # Nonuniform scale, w, signed zero and VMX denormal flushing matter.
    for lane in range(4):
        t.wf32(obj + 112 + 4 * lane, t.pick([0.0, -0.0, 1.0, -2.0, 1e-40, t.f32(-8, 8)]))
    index = t.index % 4
    t.w32(0x826065DC, index)
    t.w32(0x825C4898, (index + 1) % 4)  # render cursor must not select the slot
    t.w32(obj + 20, data)
    source = t.pick([0, external, frames + index * 64, frames + index * 64 - 16 if index else external])
    t.w32(obj + 104, source)
    t.w32(obj + 128, frames)
    if t.index % 9 == 0:
        # A subnormal times a huge finite value exposes operand flushing
        # separately from result flushing. Check all four lanes, including w.
        t.w32(obj + 104, external)
        for lane in range(4):
            t.wf32(external + 4 * lane, 1e-40)
            t.wf32(obj + 112 + 4 * lane, 1e30)
    elif t.index % 9 == 1:
        for lane in range(4):
            t.wf32(obj + 112 + 4 * lane, 1e-30)
        for p in (data + 16, external, frames + index * 64):
            for lane in range(4):
                t.wf32(p + 4 * lane, 1e-10)
    t.args(r3=obj)
