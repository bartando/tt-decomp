"""C288: apply rotations by ID, but translations only to the root (ID zero).

Covers all channel bytes, root/non-root translations, direct and remapped
rotation IDs, misses/empty maps, unsigned index boundaries, noisy flags and
record guards. The original lookup and quaternion conversion execute on both
sides. Only the entry's virtual vector getters are modeled; receiver and calls
are compared. r4 and f1 vary independently of the skeleton in r5.

Limits: readable synthetic objects, sorted maps and aligned vectors/records;
no invalid-pointer behavior, concurrent mutation or game replay. No ignored
writes or float tolerance; translation copies include arbitrary raw w bits.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_TransitionLocomotionState"
ADDRESS = 0x8224C288
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
    channel = rng.choice([0, 0, 1, 1, 2, 3, 0x7F, 0xFF, rng.randrange(256)])
    t.w8(entry + 5, channel)
    anim_id = rng.choice([0, 0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF])

    data = t.alloc(0x20, "skeletonData")
    flags = rng.getrandbits(32)
    remap = rng.choice([False, True, True])
    t.w32(data + 0x14, (flags | 2) if remap else (flags & ~2))
    indices = []
    if remap:
        count = rng.choice([0, 1, 2, 5, 9])
        ids = sorted(rng.sample([0, 1, 2, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF,
                                 rng.randrange(3, 0x7FFF), rng.randrange(0x8001, 0xFFFE)], count))
        if channel == 1 and ids and rng.random() < 0.75:
            anim_id = rng.choice(ids)
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
        indices.append(anim_id)
        t.w32(data + 0x18, 0)
        t.w16(data + 0x1C, rng.getrandbits(16))
    t.w16(entry + 6, anim_id)

    record_count = max([31, *indices]) + 1
    records = t.alloc(record_count * 0x50, "boneRecords", fill="zero")
    for i in sorted({j for index in [0, *indices] for j in (index - 1, index, index + 1)
                     if 0 <= j < record_count}):
        t.put(records + i * 0x50, rng.randbytes(0x50))
    skeleton = t.alloc(0x20, "skeleton")
    t.w32(skeleton + 4, data)
    t.w32(skeleton + 0xC, records)

    translation = t.alloc(16, "translation")
    quaternion = t.alloc(16, "quaternion")
    for i in range(4):
        t.w32(translation + 4 * i, rng.choice([0, 0x80000000, 1, 0x7F800000,
                                            0xFF800000, 0x7FC12345, rng.getrandbits(32)]))
        t.wf32(quaternion + 4 * i, rng.choice([0.0, -0.0, 1.0, -1.0, rng.uniform(-2, 2)]))
    VECTORS.update(translation=translation, quaternion=quaternion)
    t.args(r3=entry, r4=rng.getrandbits(32), r5=skeleton,
           f1=rng.choice([0.0, -1.0, 1.0, float("nan"), rng.uniform(-10, 10)]))
