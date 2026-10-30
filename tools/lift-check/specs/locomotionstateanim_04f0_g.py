"""Exact leaf lookup: direct IDs or binary search over uint16 ID/index pairs.

Covers flag noise, empty/singleton/odd/even/full uint16 counts, hits, misses,
unsigned ID boundaries, duplicate IDs with distinct indices, and unchanged
output on failure. Unused table pointers are null to catch eager dereferences.
Limits: synthetic readable, sorted tables and valid aligned object/output
pointers; no invalid-pointer behavior, concurrent mutation, or match replay.
There are no callees, stubs, float tolerances, or ignored memory ranges.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_04F0_g"
ADDRESS = 0x821D04F0
SOURCE = "src/anim/locomotion.cpp"


def inputs(t):
    rng = t.rng
    data = t.alloc(0x20, "animData")
    output = t.alloc(8, "outputWithGuards") + 2
    flags = rng.getrandbits(32)
    mode = rng.randrange(10)
    table = 0
    count = rng.randrange(0x10000)
    anim_id = rng.choice([0, 1, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF, rng.randrange(0x10000)])

    if mode == 0:
        flags &= ~2  # Direct path ignores both the table and count.
    else:
        flags |= 2
        count = rng.choice([0, 1, 2, 3, 4, 7, 8, 31, 32, 127, 256, rng.randrange(1025)])
        if mode == 9:
            count = rng.choice([0x7FFF, 0x8000, 0xFFFE, 0xFFFF])
        if count:
            if mode in (7, 8):
                # All duplicates: a lower_bound implementation would pick a different index.
                ids = [anim_id] * count
            else:
                ids = sorted(rng.sample(range(0x10000), count))
            if mode in (1, 2, 3, 9):
                anim_id = ids[rng.choice([0, count // 2, count - 1, rng.randrange(count)])]
            elif mode == 4:
                ids = [max(1, value) for value in ids]
                anim_id = 0
            elif mode == 5:
                ids = [min(0xFFFE, value) for value in ids]
                anim_id = 0xFFFF
            elif mode == 6:
                # An interior gap, with values on each side of the unsigned sign boundary.
                ids = sorted(rng.choices([0, 0x7FFF, 0x8001, 0xFFFF], k=count))
                anim_id = 0x8000
            table = t.alloc(count * 4, "idIndexPairs")
            for i, value in enumerate(ids):
                t.w16(table + i * 4, value)
                t.w16(table + i * 4 + 2, (i + 0x8123) & 0xFFFF)

    t.w32(data + 0x14, flags)
    t.w32(data + 0x18, table)
    t.w16(data + 0x1C, count)
    t.args(r3=data, r4=anim_id, r5=output)
