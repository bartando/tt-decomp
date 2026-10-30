"""Flash affine matrix concat, including out aliasing either input.

Finite and special values (signed zeros, infinities, NaNs, subnormals) in every
slot; the original's fused multiply-adds must stay fused, nothing else fused.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfConcatMatrix"
ADDRESS = 0x823FA1E0
SOURCE = "src/rage/math/swf_matrix.cpp"
FP_CONTRACT = "off"
RET = None

SPECIAL = [0, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000, 0xFF800000,
           0x7FC00000, 0x00000001, 0x80800000, 0x7F7FFFFF]


def inputs(t):
    rng = t.rng
    child = t.alloc(24, "child")
    parent = t.alloc(24, "parent")
    t.floats(child, 6, -100, 100)
    t.floats(parent, 6, -100, 100)
    for base in (child, parent):
        for k in range(6):
            if rng.random() < 0.15:
                t.w32(base + 4 * k, rng.choice(SPECIAL))
    out = rng.choice([t.alloc(24, "out"), t.alloc(24, "out"), child, parent])
    t.args(r3=out, r4=child, r5=parent)
