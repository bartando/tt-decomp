"""0x82386380: apply a crowd frame to its creature skeleton, then finalize.

Both skeleton flag paths, empty/single/multiple frames, unsigned count 0x8000,
and unrelated flag bits.
Callbacks compare entry/skeleton/zero weight and model observable output; the
unused r4 is deliberately excluded. Finalization sees the accumulated pose.
Includes callback changes to the frame array and creature's skeleton pointer:
entries reload their array, and finalization reloads self+0x24. Exact comparison,
no ignored memory. Synthetic valid objects; callback internals are boundaries.
"""
import struct
from liftcheck.spec import *

FUNCTION = "fxCrowd_ApplyAnimationFrame"
ADDRESS = 0x82386380
SOURCE = "src/graphics/fx_crowd.cpp"
TRIALS = 1000
_state = {}


def apply(ctx):
    skeleton = ctx.r(5)
    ctx.write(skeleton + 0x10, ctx.read(ctx.r(3), 4))
    if _state["mutate"]:
        ctx.write(_state["frame"] + 8, struct.pack(">I", _state["alternate"]))
        ctx.write(_state["self"] + 0x24, struct.pack(">I", _state["replacement"]))


def finish(ctx):
    ctx.write(ctx.r(3) + 0x14, ctx.read(ctx.r(3) + 0x10, 4))


CALLS = {
    "LocomotionStateAnim_C128_g": model(apply, args=("r3", "r5", "f1")),
    "LocomotionStateAnim_C288_g": model(apply, args=("r3", "r5", "f1")),
    0x8214C8F8: model(finish, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x30, "crowdCreature")
    frame = t.alloc(16, "frame")
    skeleton = t.alloc(32, "skeleton")
    replacement = t.alloc(32, "replacementSkeleton")
    data = t.alloc(32, "skeletonData")
    t.w32(obj + 0x24, skeleton)
    t.w32(skeleton + 4, data)
    t.w32(data + 20, rng.getrandbits(32))
    count = 0x8000 if t.index == 999 else [0, 1, 2, 7, 31][t.index % 5]
    entries = t.alloc(max(count, 1) * 4, "entries")
    alternate = t.alloc(max(count, 1) * 4, "alternateEntries")
    if count == 0x8000:
        entry = t.alloc(16, "largeFrameEntry")
        t.put(entries, struct.pack(">I", entry) * count)
        t.put(alternate, struct.pack(">I", entry) * count)
    else:
        for i in range(count):
            t.w32(entries + 4 * i, t.alloc(16, f"entry{i}"))
            t.w32(alternate + 4 * i, t.alloc(16, f"alternateEntry{i}"))
    t.w32(frame + 8, entries if count else 0)
    t.w16(frame + 12, count)
    _state.update(self=obj, frame=frame, alternate=alternate,
                  replacement=replacement, mutate=t.index % 3 == 0)
    t.args(r3=obj, r4=frame)
