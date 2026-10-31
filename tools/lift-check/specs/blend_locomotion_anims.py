"""Apply a translation or quaternion channel to one 0x50-byte skeleton record.

Covers channel types 0/1 and unsupported bytes, direct and remapped uint16
IDs, lookup misses, empty maps, both skeleton flag bits plus unrelated noise,
record flag words (including zero), and full uint16 destination indices. All four
translation lanes are copied as raw bits; quaternion conversion and ID lookup
execute their original code. The unused r4 and f1 inputs vary independently.

Limits: synthetic readable objects and sorted ID maps, aligned skeleton records
and arbitrary translation-pointer alignment, no concurrent mutation or invalid-pointer behavior. Only
the entry's two virtual getters are modeled, returning readable test vectors;
their calls and receiver are compared. No ignored writes or float tolerance.
The odd rlwimi tests at C1B0/C254 always produce a nonzero value: they do not
filter channels based on record flags, skeleton flags, or a nonzero ID.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_C128_g"
ADDRESS = 0x8224C128
SOURCE = "src/anim/locomotion.cpp"
TRIALS = 1000

VECTORS = {}
CALLS = {
    "LocomotionStateAnim_04F0_g": run(),
    0x8223AD30: run(),
    "entry.vfn_14": model(lambda ctx: ctx.ret(r3=VECTORS["translation"]), args=("r3",)),
    "entry.vfn_15": model(lambda ctx: ctx.ret(r3=VECTORS["quaternion"]), args=("r3",)),
}


def inputs(t):
    rng = t.rng
    entry = t.alloc(0x10, "entry")
    t.w32(entry, t.vtable("entry", 16))
    channel = rng.choice([0, 0, 1, 1, 2, 3, 0x7F, 0xFF, rng.randrange(2, 256)])
    t.w8(entry + 5, channel)

    data = t.alloc(0x20, "skeletonData")
    flags = rng.getrandbits(32)
    remap = rng.choice([False, True, True])
    flags = (flags | 2) if remap else (flags & ~2)
    t.w32(data + 0x14, flags)
    indices = []
    if remap:
        count = rng.choice([0, 1, 2, 5, 9])
        ids = sorted(rng.sample([0, 1, 2, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF,
                                 rng.randrange(3, 0x7FFF), rng.randrange(0x8001, 0xFFFE)], count))
        anim_id = rng.choice(ids) if ids and rng.random() < 0.75 else rng.randrange(0x10000)
        table = t.alloc(max(4, count * 4), "idMap")
        for i, value in enumerate(ids):
            index = (rng.choice([0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
                     if rng.randrange(32) == 0 else rng.randrange(32))
            indices.append(index)
            t.w16(table + 4 * i, value)
            t.w16(table + 4 * i + 2, index)
        t.w32(data + 0x18, table if count else 0)
        t.w16(data + 0x1C, count)
    else:
        anim_id = rng.choice([0, 1, 7, 31, rng.randrange(32)])
        if rng.randrange(32) == 0:
            anim_id = rng.choice([0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
        indices.append(anim_id)
        # A direct lookup must not touch the map pointer or count.
        t.w32(data + 0x18, 0)
        t.w16(data + 0x1C, rng.getrandbits(16))
    t.w16(entry + 6, anim_id)

    record_count = max([31, *indices]) + 1
    records = t.alloc(record_count * 0x50, "boneRecords", fill="zero")
    # Keep the full array readable, randomizing each candidate and its neighbors.
    for i in sorted({j for index in [0, *indices] for j in (index - 1, index, index + 1)
                     if 0 <= j < record_count}):
        t.put(records + i * 0x50, rng.randbytes(0x50))
        t.w32(records + i * 0x50 + 0x48, rng.choice([0, 1, 0xE, 0x80, 0x300,
                                                   0xFFFFFFFF, rng.getrandbits(32)]))
    skeleton = t.alloc(0x20, "skeleton")
    t.w32(skeleton + 4, data)
    t.w32(skeleton + 0xC, records)

    translation = t.alloc(16, "translation")
    quaternion = t.alloc(16, "quaternion")
    # Include signed zeros, infinities and NaN payloads in the raw vector copy.
    for i in range(4):
        t.w32(translation + 4 * i, rng.choice([0, 0x80000000, 1, 0x7F800000,
                                            0xFF800000, 0x7FC12345, rng.getrandbits(32)]))
        t.wf32(quaternion + 4 * i, rng.choice([0.0, -0.0, 1.0, -1.0, rng.uniform(-2, 2)]))
    VECTORS.update(translation=translation + t.index % 16, quaternion=quaternion)
    t.args(r3=entry, r4=rng.getrandbits(32), r5=skeleton,
           f1=rng.choice([0.0, -1.0, 1.0, float("nan"), rng.uniform(-10, 10)]))
