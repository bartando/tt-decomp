"""Read the indexed weight through the pointer at animPair[1]+0x10.

Covers types 0/1 and invalid bytes, direct/remapped IDs, empty maps, misses,
uint16 index boundaries, negative/positive weights, signed zero, subnormals,
infinities and quiet NaNs. Lookup runs its original code. Invalid types use
null pair/output pointers, and misses have a null weight object, catching eager
accesses. Output guards and unchanged failure output compare exactly.

Limits: readable synthetic objects and sorted maps; default FP environment,
no signaling NaNs, concurrent mutation or game replay. No stubs, ignored writes
or float tolerance. The self argument is unused and varies independently.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_81A8"
ADDRESS = 0x822481A8
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 240
EXTERNS = {'g_floatZero': 0x8202D110}
CALLS = {"LocomotionStateAnim_04F0_g": run()}


def inputs(t):
    rng = t.rng
    channel = rng.choice([0, 0, 1, 1, 2, 3, 0x7F, 0xFF, rng.randrange(256)])
    anim_id = rng.choice([0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
    if channel > 1:
        t.args(r3=rng.getrandbits(32), r4=channel | (rng.getrandbits(24) << 8), r5=anim_id | (rng.getrandbits(16) << 16), r6=0, r7=0)
        return

    data = t.alloc(0x20, "animData")
    pair = t.alloc(8, "animPair")
    output = t.alloc(12, "outputWithGuards") + 4
    t.w32(pair, data)
    flags = rng.getrandbits(32)
    remap = rng.choice([False, True, True])
    t.w32(data + 0x14, (flags | 2) if remap else (flags & ~2))
    indices = [anim_id] if not remap else []
    if remap:
        count = rng.choice([0, 1, 2, 5, 9])
        ids = sorted(rng.sample([0, 1, 2, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF,
                                 rng.randrange(3, 0x7FFF), rng.randrange(0x8001, 0xFFFE)], count))
        if ids and rng.random() < 0.75:
            anim_id = rng.choice(ids)
        table = t.alloc(max(4, count * 4), "idMap")
        for i, value in enumerate(ids):
            index = rng.choice([0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
            indices.append(index)
            t.w16(table + 4 * i, value)
            t.w16(table + 4 * i + 2, index)
        t.w32(data + 0x18, table if count else 0)
        t.w16(data + 0x1C, count)
        found = anim_id in ids
    else:
        t.w32(data + 0x18, 0)
        t.w16(data + 0x1C, rng.getrandbits(16))
        found = True

    if found:
        weights = t.alloc((max(indices) + 1) * 4, "weights", fill="zero")
        bits = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x807FFFFF,
                0x3F800000, 0xBF800000, 0x7F800000, 0xFF800000,
                0x7FC12345, 0xFFC12345, 0x3E800000, 0xBE800000]
        for index in indices:
            t.w32(weights + index * 4, rng.choice(bits))
        weight_object = t.alloc(0x20, "weightObject")
        t.w32(weight_object + 0x10, weights)
        t.w32(pair + 4, weight_object)
    else:
        t.w32(pair + 4, 0)
    t.args(r3=rng.getrandbits(32), r4=channel | (rng.getrandbits(24) << 8), r5=anim_id | (rng.getrandbits(16) << 16), r6=pair, r7=output)
