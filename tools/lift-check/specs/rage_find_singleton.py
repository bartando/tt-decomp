"""Singleton interval lookup, signed offsets, and the 32-byte removal path."""
from liftcheck.spec import *

FUNCTION = "rage_FindSingleton"
ADDRESS = 0x820F90D0
SOURCE = "src/rage/core/rage_core_utils.cpp"
TRIALS = 1000
EXTERNS = {"g_templateRegistry": 0x82607C40}
CALLS = {
    "game_94F0": run(deref={"r4": 8}),
    "datResourceMgr_RemoveEntry": stub(ret="void", args=("r3",)),
    "_locale_register": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    registry = t.sym("lbl_82607C40")
    # A wide interval exercises signed overflow in value - start.
    if t.rng.randrange(8) == 0:
        t.w32(registry, t.pick([0, 1, 0x100, 0x7FFFFFFF]))
        t.w32(registry + 4, 0xFFFFFFFF)
        t.w32(registry + 0x10000, 1)
        t.args(r3=t.pick([0x80000000, 0x80000001, 0xFFFFFFFF]))
        return
    count = t.pick([0, 1, 2, 3, 5, 8])
    base = t.pick([0x80000000, 0x90000000, 0xFFFFF000])
    for i in range(count):
        start = base + 128 * i
        t.w32(registry + 8 * i, start)
        t.w32(registry + 8 * i + 4, start + t.pick([0, 16, 32, 63]))
    t.w32(registry + 0x10000, count)
    if count:
        start = base + 128 * t.rng.randrange(count)
        value = t.pick([start - 1, start, start + 1, start + 16, start + 31,
                        start + 32, start + 33, start + 63, start + 64, t.u32()])
    else:
        value = t.u32()
    t.args(r3=value & 0xFFFFFFFF)
