"""Mapped animation weights, with the original ID lookup executed on both sides.

Modes 0/1, direct/remapped IDs, empty maps/misses, uint16 lookup boundaries,
negative slot sentinels and distinct mapped slots; signed zero, subnormals,
infinities and quiet NaNs. Invalid modes have null pair/output, misses have
null slot/weight tables, and negative slots have a null weight table. All
memory and the bool return compare exactly (no ignores or tolerance).
Readable sorted maps, default FP environment; no signaling NaNs or races.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_GetMappedWeight"
ADDRESS = 0x82248250
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
CALLS = {"LocomotionStateAnim_04F0_g": run()}


def inputs(t):
    r = t.rng
    mode = r.choice([0, 0, 1, 1, 2, 3, 127, 255, r.randrange(256)])
    anim_id = r.choice([0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
    if mode > 1:
        t.args(r3=t.u32(), r4=mode, r5=anim_id, r6=0, r7=0)
        return
    data = t.alloc(0x20, "animationData")
    pair = t.alloc(16, "animPair")
    output = t.alloc(12, "outputAndGuards") + 4
    t.w32(pair, data)
    remap = r.choice([False, True, True])
    t.w32(data + 0x14, (t.u32() & ~2) | (2 if remap else 0))
    indices = [anim_id] if not remap else []
    found = True
    if remap:
        count = r.choice([0, 1, 2, 5, 9])
        ids = sorted(r.sample([0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF,
                               r.randrange(32, 0x7FFF)], count))
        if ids and r.random() < 0.75:
            anim_id = r.choice(ids)
        table = t.alloc(max(4, count * 4), "idMap")
        for i, value in enumerate(ids):
            index = r.choice([0, 1, 7, 31, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
            indices.append(index)
            t.w16(table + 4 * i, value)
            t.w16(table + 4 * i + 2, index)
        t.w32(data + 0x18, table if count else 0)
        t.w16(data + 0x1C, count)
        found = anim_id in ids
    if found:
        slots = t.alloc((max(indices) + 1) * 4, "slotMap", fill="zero")
        t.w32(pair + 4, slots)
        negative = r.choice([False, False, True])
        weights = 0 if negative else t.alloc(256, "weights")
        t.w32(pair + 12, weights)
        bits = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x807FFFFF,
                0x3F800000, 0xBF800000, 0x7F800000, 0xFF800000,
                0x7FC12345, 0xFFC12345, 0x3E800000, 0xBE800000]
        for index in indices:
            slot = r.choice([0x80000000, 0xFFFFFFFF, 0x80000001]) if negative else r.randrange(64)
            t.w32(slots + 4 * index, slot)
        if weights:
            for i in range(64):
                t.w32(weights + 4 * i, r.choice(bits))
    else:
        t.w32(pair + 4, 0)
        t.w32(pair + 12, 0)
    t.args(r3=t.u32(), r4=mode, r5=anim_id, r6=pair, r7=output)
