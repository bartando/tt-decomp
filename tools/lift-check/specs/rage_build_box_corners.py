"""0x82147EF8: eight AABB corners, center +/- fullSize/2, retaining center.w.

Exercise nonuniform/signed/flat sizes, arbitrary w bits, guards, VMX denormal
flushing and infinities/NaNs. Also cover aligned aliases: either input may
occupy any output slot, and the two inputs may coincide. Compare every byte
(no ignored ranges), FTOL=0. Inputs are aligned and backed by readable vec4s;
misaligned VMX addressing and FP exception flags are outside this proof.
"""
from liftcheck.spec import *

FUNCTION = "rage::buildBoxCorners"
ADDRESS = 0x82147EF8
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    storage = t.alloc(160, "cornersAndGuards", floats=[(16, 32)])
    out = storage + 16
    # Random backing makes bogus array-style reads differ from a broadcast.
    center = t.alloc(176, "centerAndGuard") + 16
    size = t.alloc(176, "sizeAndGuard") + 16
    kind = rng.randrange(12)
    if kind == 7:
        center = out + 16 * rng.randrange(8)
    elif kind == 8:
        size = out + 16 * rng.randrange(8)
    elif kind == 9:
        center = size
    elif kind == 10:
        center = size = out + 16 * rng.randrange(8)
    values = [rng.uniform(-1000, 1000) for _ in range(3)]
    sizes = [rng.uniform(-100, 100) for _ in range(3)]
    if kind == 0:
        sizes = [0.0, -0.0, 0.0]
    elif kind == 1:
        sizes[rng.randrange(3)] = 0.0
    elif kind == 2:
        sizes = [2.0, 6.0, 10.0]
    elif kind == 3:
        sizes = [rng.choice((2.0**-149, -2.0**-148, 2.0**-126)) for _ in range(3)]
        values = [0.0] * 3
    elif kind == 4:
        sizes = [rng.choice((float("inf"), -float("inf"), float("nan"))) for _ in range(3)]
    elif kind == 5:
        values = [rng.choice((float("inf"), -float("inf"), float("nan"))) for _ in range(3)]
    elif kind == 6:
        values = [rng.choice((2.0**-149, -2.0**-148, -0.0)) for _ in range(3)]
    for lane in range(3):
        t.wf32(center + 4 * lane, values[lane])
        t.wf32(size + 4 * lane, sizes[lane])
    # The fourth lane is copied bit-for-bit, never recomputed.
    t.w32(center + 12, rng.choice((0, 0x80000000, 0x7fc12345, rng.getrandbits(32))))
    t.w32(size + 12, rng.getrandbits(32))
    t.args(r3=out, r4=center, r5=size)
