"""Interval search uses the global table, including asymmetric key pairs."""
from liftcheck.spec import *

FUNCTION = "game_94F0"
ADDRESS = 0x820F94F0
SOURCE = "src/game/template_registry.cpp"
TRIALS = 1000
EXTERNS = {"g_templateRegistry": 0x82607C40}


def inputs(t):
    registry = t.sym("lbl_82607C40")
    # Overlap plus unequal key words makes the direction comparison observable.
    if t.rng.randrange(8) == 0:
        for i, (start, end) in enumerate([(100, 250), (200, 210), (300, 310)]):
            t.w32(registry + 8 * i, start)
            t.w32(registry + 8 * i + 4, end)
        t.w32(registry + 0x10000, 3)
        key = t.alloc(8, "key")
        t.w32(key, 199)
        t.w32(key + 4, 200)
        t.args(r3=t.alloc(16, "ignored_registry", fill="zero"), r4=key)
        return
    count = t.pick([0, 1, 2, 3, 4, 7, 16, 31])
    entries = []
    base = t.pick([0, 0x100, 0x7FFFFE00, 0x80000000, 0xFFFFF000])
    for i in range(count):
        start = base + i * 64
        end = start + t.pick([0, 1, 16, 32, 63])
        entries.append((start, end))
        t.w32(registry + 8 * i, start)
        t.w32(registry + 8 * i + 4, end)
    t.w32(registry + 0x10000, count)
    if entries:
        start, end = t.pick(entries)
        k1 = t.pick([start - 1, start, start + 1, end, end + 1, t.u32()]) & 0xFFFFFFFF
        k2 = t.pick([start - 1, start, end, end + 1, k1, t.u32()]) & 0xFFFFFFFF
    else:
        k1, k2 = t.u32(), t.u32()
    key = t.alloc(8, "key")
    t.w32(key, k1)
    t.w32(key + 4, k2)
    decoy = t.alloc(16, "ignored_registry", fill="zero")
    t.args(r3=decoy, r4=key)
