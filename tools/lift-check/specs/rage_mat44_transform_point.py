"""4x4 point transform, including out aliasing the point.

Finite values plus special values in random slots. Lane-specific fused
accumulation order must match: FP_CONTRACT is off, everything fused is explicit.
"""
from liftcheck.spec import *

FUNCTION = "rage::mat44TransformPoint"
ADDRESS = 0x8214EA10
SOURCE = "src/rage/math/mat44.cpp"
FP_CONTRACT = "off"
RET = None

SPECIAL = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000, 0x00000001, 0x7F7FFFFF]


def inputs(t):
    rng = t.rng
    matrix = t.alloc(64, "matrix")
    point = t.alloc(16, "point")
    t.floats(matrix, 16, -1000, 1000)
    t.floats(point, 4, -1000, 1000)
    for base, n in ((matrix, 16), (point, 4)):
        for k in range(n):
            if rng.random() < 0.05:
                t.w32(base + 4 * k, rng.choice(SPECIAL))
    out = rng.choice([t.alloc(16, "out"), t.alloc(16, "out"), point])
    t.args(r3=matrix, r4=point, r5=out)
