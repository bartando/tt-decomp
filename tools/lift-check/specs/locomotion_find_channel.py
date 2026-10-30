"""24-bit channel-key binary search, including the exact midpoint/insertion index.

Exercise empty/singleton, odd/even and full uint16 counts, hits at all positions,
misses before/inside/after the table, duplicate keys with distinct pointers, both
key components' boundaries, and ignored entry padding/count capacity. All memory,
return pointers and preserved registers compare exactly; no callees or exclusions.
Limits: sorted readable tables and disjoint aligned output; no concurrent writes.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_FindChannelByKey"
ADDRESS = 0x8224A390
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x30, "animation")
    output = t.alloc(12, "indexWithGuards") + 4
    mode = rng.randrange(16)
    count = rng.choice((0, 1, 2, 3, 4, 7, 8, 31, 32, 127, 256, rng.randrange(513)))
    if mode == 15:
        count = rng.choice((0x7FFF, 0x8000, 0xFFFE, 0xFFFF))
    query = rng.choice((0, 1, 0xFFFF, 0x10000, 0x7FFFFF, 0x800000,
                        0xFF0000, 0xFFFFFF, rng.randrange(1 << 24)))
    if mode == 7:
        keys = [query] * count  # A lower_bound replacement returns the wrong duplicate.
    else:
        keys = sorted(rng.sample(range(1 << 24), count))
    if count and mode in (0, 1, 2, 3, 8, 9, 15):
        query = keys[rng.choice((0, count // 2, count - 1, rng.randrange(count)))]
    elif mode == 4:
        keys = [max(1, key) for key in keys]
        query = 0
    elif mode == 5:
        keys = [min(0xFFFFFE, key) for key in keys]
        query = 0xFFFFFF
    elif mode == 6:
        keys = sorted(rng.choices((0, 0x7FFFFF, 0x800001, 0xFFFFFF), k=count))
        query = 0x800000
    table = 0
    if count:
        # Padding byte +1 must not become part of the key; use separate pointers.
        entries = t.alloc(count * 4, "keys", fill=b"".join(
            struct.pack(">BBH", key >> 16, rng.randrange(256), key & 0xFFFF) for key in keys))
        table = t.alloc(count * 4, "keyPointers", fill=b"".join(
            struct.pack(">I", entries + i * 4) for i in range(count)))
    t.w32(obj + 0x24, table)
    t.w16(obj + 0x28, count)
    t.args(r3=obj, r4=query >> 16, r5=query & 0xFFFF, r6=output)
