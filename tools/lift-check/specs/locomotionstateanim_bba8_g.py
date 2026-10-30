"""Pose-to-channel dispatch at 0x8224BBA8.

Covers both supported types, unsupported byte types, direct and mapped
uint16 IDs (including 0/0x7FFF/0x8000/0xFFFF), lookup hits/misses, remapped
indices, packed root/non-root translation, every active mask bit, unrelated
flag noise, quaternion conversion, and each of the three virtual slots.
The lookup, matrix-to-quaternion helper, and sqrt execute original PPC.
Virtual callbacks compare this/data arguments and all 16 payload bytes, then
copy the payload into the channel so memory effects are also observable.
Unused data pointers are null on no-op paths to catch eager dereferences.

Limits: synthetic valid aligned objects, sorted unique lookup tables, finite
matrix entries, default FP rounding. Virtual methods are modeled consumers,
not actual channel implementations; no match replay, invalid-pointer behavior,
concurrent mutation, FPSCR flags, or NaN payload testing. Exact comparison;
no ignored writes or float tolerance. The target has no FP instructions.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_BBA8_g"
ADDRESS = 0x8224BBA8
SOURCE = "src/anim/locomotion.cpp"
TRIALS = 2000


def _apply(ctx):
    ctx.write(ctx.r(3) + 0x10, ctx.read(ctx.r(4), 16))


def _reset(ctx):
    ctx.write(ctx.r(3) + 0x10, bytes(16))


CALLS = {
    "LocomotionStateAnim_04F0_g": run(),
    "LocomotionStateAnim_B218_g": run(),
    "rage::phBoundCapsule_01D0_g": run(),
    "channel.vfn_13": model(_reset, args=("r3",)),
    "channel.vfn_17": model(_apply, args=("r3", "r4"), deref={"r4": 16}),
    "channel.vfn_18": model(_apply, args=("r3", "r4"), deref={"r4": 16}),
}


def inputs(t):
    rng = t.rng
    channel = t.alloc(0x30, "channel")
    t.w32(channel, t.vtable("channel", slots=19))
    channel_type = rng.choice([0, 0, 1, 1, rng.randrange(2, 256)])
    anim_id = rng.choice([0, 0, 1, 0x7FFF, 0x8000, 0xFFFF, rng.randrange(0x10000)])
    t.w8(channel + 5, channel_type)
    t.w16(channel + 6, anim_id)
    context = t.alloc(0x10, "poseContext")
    t.w32(context + 4, 0)
    t.w32(context + 0x0C, 0)
    t.args(r3=channel, r4=rng.getrandbits(32), r5=context)
    if channel_type > 1:
        return

    anim_data = t.alloc(0x20, "animData")
    t.w32(context + 4, anim_data)
    flags = rng.getrandbits(32)
    mapped = rng.choice([False, True, True])
    flags = (flags | 2) if mapped else (flags & ~2)
    t.w32(anim_data + 0x14, flags)
    t.w32(anim_data + 0x18, 0)
    t.w16(anim_data + 0x1C, rng.randrange(0x10000))
    index = anim_id
    if mapped:
        hit = rng.randrange(5) != 0
        ids = sorted(set(rng.sample(range(0x10000), rng.randrange(9))) | {anim_id})
        if not hit:
            ids.remove(anim_id)
        table = t.alloc(len(ids) * 4, "idIndexPairs") if ids else 0
        t.w32(anim_data + 0x18, table)
        t.w16(anim_data + 0x1C, len(ids))
        for i, value in enumerate(ids):
            mapped_index = rng.choice([0, 1, 7, 31, rng.randrange(64)])
            if value == anim_id:
                index = mapped_index
            t.w16(table + i * 4, value)
            t.w16(table + i * 4 + 2, mapped_index)
        if not hit:
            return

    # Include the full uint16 direct-index range without randomizing unused MBs.
    records = t.alloc((index + 1) * 0x50, "poseRecords", fill="zero")
    t.w32(context + 0x0C, records)
    record = records + index * 0x50
    t.floats(record, 20, -10, 10)
    active = rng.choice([0, 1, 2, 4, 8, 0x10, 0x40, 0x80, 0x100, 0x200, 0x380, 0x38F])
    t.w32(record + 0x48, (rng.getrandbits(32) & ~0x38F) | active)
