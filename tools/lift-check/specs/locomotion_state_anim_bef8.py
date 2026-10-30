"""BEF8: binary search of sorted (type byte, uint16 ID) channel pointers.

Exercises empty/singleton/odd/even arrays, hits throughout the table, duplicates,
misses before/between/after keys, uint16 count and unsigned key boundaries,
and noisy upper argument/count bits. Table entries and guards are random
and must stay intact.
No callees, ignored writes or tolerance. Synthetic readable sorted tables;
invalid pointers, concurrent edits and game replay are outside this spec.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim::FindAnimationByID"
ADDRESS = 0x8224BEF8
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    count = (rng.choice([0x7FFF, 0x8000, 0xFFFF]) if rng.randrange(64) == 0
             else rng.choice([0, 1, 2, 3, 4, 7, 8, 15, 32, 63, 128]))
    edges = [0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x10000, 0x10001,
             0x7FFFFF, 0x800000, 0xFF0000, 0xFF7FFF, 0xFF8000, 0xFFFFFF]
    keys = sorted(rng.choices(edges + [rng.randrange(1 << 24) for _ in range(min(count, 128))], k=count))
    table = t.alloc(max(4, 4 * count), "channels")
    entries = {}
    for i, key in enumerate(keys):
        # Large count boundaries can reuse equal-key channels; small tables
        # keep distinct duplicates so the exact midpoint result is checked.
        if count <= 128 or key not in entries:
            entry = t.alloc(16, f"channel{i}")
            t.w8(entry + 5, key >> 16)
            t.w16(entry + 6, key)
            entries[key] = entry
        t.w32(table + 4 * i, entries[key])
    key = rng.choice(edges + [rng.randrange(1 << 24)])
    if keys and rng.randrange(4) != 0:
        key = rng.choice(keys)
    frame = t.alloc(32, "frame")
    t.w32(frame + 8, table if count else 0)
    t.w16(frame + 12, count)
    # r4 supplies the type's low byte, r5 the full low halfword.
    t.args(r3=frame, r4=(rng.getrandbits(24) << 8) | (key >> 16),
           r5=(rng.getrandbits(16) << 16) | (key & 0xFFFF))
