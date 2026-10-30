"""0x82118278: row-vector XYZ Euler rotation, nine floats in padded rows.

All zero-axis combinations, negative zero, small/general angles, and exact or
partially overlapping input/output. Original sin/cos and CRT callees execute;
compare the nine results, untouched row padding, translation and guards exactly.
Finite float32 angles and default FP rounding; no tolerance or ignored bytes.
"""
from liftcheck.spec import *

FUNCTION = "rage::mat33FromEuler"
ADDRESS = 0x82118278
SOURCE = "src/rage/math/mat33.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
CALLS = {0x820D04F0: run(args=("r3", "r4", "f1")),
         0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    rng = t.rng
    storage = t.alloc(112, "matrixAndGuards")
    out = storage + 16
    overlap = t.index % 5
    angles = out + [0, 4, 16, 32][overlap] if overlap < 4 else t.alloc(16, "angles")
    for axis in range(3):
        value = rng.choice([-0.0, 0.0]) if t.index % 8 & (1 << axis) else rng.choice([
            rng.uniform(-20, 20), 2.0**-40, -2.0**-30, 3.1415927410125732])
        t.wf32(angles + axis * 4, value)
    t.args(r3=out, r4=angles)
