"""0x8224C418: r6 is unused, r7 is the pose; vector/quaternion slots are 17/18.

Execute the real sorted-channel lookup and compare its full uint32 arguments.
Cover both hits, either/both misses, identical channel IDs and aliased payloads.
The first setter changes the second channel's vtable and the quaternion payload,
so the second dispatch must reload both. r6 is distinct decoy data or junk on
no-op paths. Every call, return, input, output and guard byte compares exactly.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim::SetupAnimationPair"
ADDRESS = 0x8224C418
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000


def set_vector(ctx):
    channel, payload = ctx.r(3), ctx.r(4)
    ctx.write(channel + 0x10, ctx.read(payload, 16))
    second, vtable = struct.unpack('>II', ctx.read(channel + 0x30, 8))
    ctx.write(second, struct.pack('>I', vtable))
    # The caller must forward the live original pointer on the second call.
    ctx.write(payload - 16, bytes.fromhex('3f800000400000004040000040800000'))


def set_quaternion(ctx):
    ctx.write(ctx.r(3) + 0x10, ctx.read(ctx.r(4), 16))


CALLS = {
    "LocomotionStateAnim::FindAnimationByID": run(),
    "initial.vfn_17": model(set_vector, args=("r3", "r4"), deref={"r4": 16}),
    "changed.vfn_18": model(set_quaternion, args=("r3", "r4"), deref={"r4": 16}),
}


def inputs(t):
    rng = t.rng
    mode = t.index % 8
    type1 = rng.choice((0, 1, 5, 6, 255, rng.randrange(256)))
    type2 = type1 if mode in (4, 5) else type1 ^ rng.choice((1, 2, 128))
    id1 = (rng.getrandbits(24) << 8) | type1
    id2 = (rng.getrandbits(24) << 8) | type2
    first_key, second_key = (type1, 0), (type2, 0)
    keys = {(rng.randrange(256), rng.randrange(1, 65536)) for _ in range(rng.randrange(9))}
    if mode not in (1, 3, 5):
        keys.add(first_key)
    if mode not in (2, 3, 5):
        keys.add(second_key)
    # A matching type with a nonzero ID must not satisfy either lookup.
    keys.update(((type1, 1), (type2, 65535)))
    if t.index % 16 == 13:
        keys.clear()
    frame = t.alloc(0x30, 'frame with guards')
    table = t.alloc(max(4, len(keys) * 4), 'sorted channels')
    entries = {}
    initial, changed = t.vtable('initial', 19), t.vtable('changed', 19)
    for i, key in enumerate(sorted(keys)):
        entry = t.alloc(0x50, f'channel {key}')
        t.w32(entry, initial)
        t.w8(entry + 5, key[0])
        t.w16(entry + 6, key[1])
        t.w32(table + i * 4, entry)
        entries[key] = entry
    t.w32(frame + 8, table if keys else 0)
    t.w16(frame + 12, len(keys))
    pose = t.alloc(64, 'pose with guards') + 16
    t.floats(pose, 8, -50, 50)
    decoy = t.alloc(64, 'unused r6 decoy with guards') + 16
    t.floats(decoy, 8, 100, 200)
    if first_key in entries and second_key in entries:
        first, second = entries[first_key], entries[second_key]
        t.w32(first + 0x30, second)
        t.w32(first + 0x34, changed)
        if mode == 6:
            pose = first + 0x10
    else:
        # Neither the param nor unused slot may be dereferenced on a miss.
        pose = rng.choice((0, pose))
        decoy = rng.getrandbits(32)
    t.args(r3=frame, r4=id1, r5=id2, r6=decoy, r7=pose)
