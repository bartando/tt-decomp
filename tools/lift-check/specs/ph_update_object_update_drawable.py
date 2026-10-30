"""0x8227DA40: gated drawable update; check every byte of variable-size poses."""
import struct
from liftcheck.spec import *

FUNCTION = "phUpdateObject::UpdateDrawable"
ADDRESS = 0x8227DA40
SOURCE = "src/physics/ph_update_object.cpp"
TRIALS = 1000


def transform(ctx):
    ctx.write(ctx.r(3), bytes(b ^ 0x5A for b in ctx.read(ctx.r(3), 64)))


def draw(ctx):
    expected, size = struct.unpack(">II", ctx.read(ctx.r(3) + 4, 8))
    assert ctx.read(ctx.r(4), size) == ctx.read(expected, size), "drawable pose bytes differ"


CALLS = {
    "_RtlCheckStack12": run(transparent=True),
    "mat44ComposeAffineInPlace": model(transform, args=("r3", "r4"), deref={"r3": 64, "r4": 64}),
    "drawable.vfn_5": model(draw, args=("r3", "r4", "r5", "r6", "r7")),
}


def inputs(t):
    obj = t.alloc(0x90, "updateObject")
    drawable = t.alloc(16, "drawable")
    t.w32(drawable, t.vtable("drawable"))
    mode = t.pick(["inactive", "noDrawable", "direct", "animated", "collider"])
    t.w8(obj + 0x85, 0 if mode == "inactive" else t.pick([1, 2, 255]))
    t.w32(obj + 0x60, 0 if mode == "noDrawable" else drawable)
    t.w32(obj + 0x6C, 0)
    frame_bytes = t.rng.randbytes(64)
    frame = t.alloc(64, "frame", fill=frame_bytes)
    anim = t.alloc(0x60, "animation")
    t.w8(anim + 24, 1 if mode == "animated" else 0)
    t.w32(0x826063C4, anim)
    expected = frame_bytes
    if mode == "animated":
        expected = bytes(b ^ 0x5A for b in expected)
    if mode == "collider":
        # Includes >4096 bytes: a fixed-size truncating stack buffer is incorrect.
        count = t.pick([1, 2, 17, 64, 65, 96])
        index = t.pick([0, 1, 3, 7])
        collider = t.alloc(0x30, "collider")
        state = t.alloc(0x20, "state")
        array = t.alloc(64, "poseArray")
        expected = t.rng.randbytes(count * 64)
        pose = t.alloc(len(expected), "pose", fill=expected)
        # Valid decoy catches the old state+24 / collider+24 confusion.
        decoy = t.alloc(len(expected), "decoyPose")
        decoy_array = t.alloc(64, "decoyArray")
        for i in range(8):
            t.w32(array + 8 * i, pose if i == index else decoy)
            t.w32(decoy_array + 8 * i, decoy)
        t.w32(obj + 0x6C, collider)
        t.w32(collider + 4, state)
        t.w32(collider + 24, array)
        t.w16(collider + 34, index)
        t.w16(state + 12, count)
        t.w32(state + 24, decoy_array)
    reference = t.alloc(len(expected), "expectedPose", fill=expected)
    t.w32(drawable + 4, reference)
    t.w32(drawable + 8, len(expected))
    t.args(r3=obj, r4=frame, r5=t.u32())
