"""Debug fill in both modes, including zero length, tails and address wrap bytes.

The buffer is mapped and word-aligned, as expected by the original word stores.
Whole-buffer comparison checks the untouched guards on both sides of the fill.
"""
from liftcheck.spec import *

FUNCTION = "rage_stricmp_6358"
ADDRESS = 0x821862A0
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
TRIALS = 1000
EXTERNS = {"g_sysMemDebugFillFlag": 0x8260642D}


def inputs(t):
    size = t.rng.choice((0, 1, 2, 3, 4, 5, 7, 8, 15, 16, 31, 63, 255, 256, 257, t.rng.randrange(513)))
    buf = t.alloc(544, "buffer_and_guards")
    offset = 4 * t.rng.randrange(1, 8)
    t.w8(EXTERNS["g_sysMemDebugFillFlag"], t.rng.choice((0, 0, 1, 2, 255)))
    t.args(r3=buf + offset, r4=size)
