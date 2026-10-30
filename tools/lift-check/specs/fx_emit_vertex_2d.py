"""2D vertex emission and the null-cursor count-only pass."""
from liftcheck.spec import *

FUNCTION = "fxEmitVertex2D"
ADDRESS = 0x82406010
SOURCE = "src/graphics/fx_billboard.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    rng = t.rng
    # Guard bytes around the single vertex catch stray writes and wrong stride.
    vertices = t.alloc(68, "vertex")
    count_only = rng.choice([0, 1, 0xFFFFFFFF])
    cursor = 0 if count_only and rng.randrange(2) == 0 else vertices + 16
    t.w32(0x825EBA74, cursor)
    t.w32(0x825EBA84, count_only)
    t.w32(0x825EBA88, rng.choice([0, 0xFFFFFFFF, rng.getrandbits(32)]))
    t.w32(0x825CA604, rng.getrandbits(32))
    for address in (0x825EBA6C, 0x825EBA80, 0x825EBA8C, 0x825EBA78, 0x825EBA70):
        t.wf32(address, rng.uniform(-1000, 1000))
    t.args(f1=rng.uniform(-1000, 1000), f2=rng.uniform(-1000, 1000))
