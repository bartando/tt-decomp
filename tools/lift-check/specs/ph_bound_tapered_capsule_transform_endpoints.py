"""0x8233AB98 slot 3: world cap centres and normalized endpoint difference.

Run the actual base transform too. Exercise enabled byte (including non-1),
zero/signed/negative length, nonsymmetric scale/shear/translation, arbitrary w,
NaN/infinity/subnormal operands, degenerate axes, and matrix aliasing endpoint
scratch. Compare every write and base-call pointer/content, with no ignores or
tolerance. Dirty=0 must not even dereference the matrix.

The VMX rsqrt is the harness's exact estimate, not console accuracy evidence.
All written bits compare exactly; FP status is outside this comparison.
"""
from liftcheck.spec import *

FUNCTION = "rage::phBoundTaperedCapsule::TransformEndpoints"
ADDRESS = 0x8233AB98
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
CALLS = {0x8228D0E8: run(args=("r3", "r4"), deref={"r4": 64})}


def inputs(t):
    rng = t.rng
    bound = t.alloc(0x120, "capsuleAndGuards") + 16
    t.floats(bound, 0x100 // 4, -100, 100)
    enabled = (0, 1, 2, 255)[t.index % 4]
    t.w8(bound + 7, enabled)
    matrix = t.alloc(96, "matrixAndGuards") + 16
    # Also exercise overlapping matrices: the original reloads after stores.
    if t.index % 9 == 0:
        matrix = bound + rng.choice((0x20, 0x30, 0xB0, 0xC0))
    t.floats(matrix, 16, -10, 10)
    kind = t.index % 10
    if kind == 0:
        for i in range(16):
            t.wf32(matrix + i * 4, 1. if i in (0, 5, 10, 15) else 0.)
    elif kind == 1:
        for i in range(16):
            t.wf32(matrix + i * 4, 0.)
    elif kind == 2:
        t.w32(matrix + 4 * rng.randrange(16), rng.choice((
            1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.wf32(bound + 0x90, rng.choice((0., -0., 1., -1., 1e-20, rng.uniform(-100, 100))))
    if kind == 3:
        t.w32(bound + 0x30 + 4 * rng.randrange(4), rng.choice((
            1, 0x807FFFFF, 0x7F800000, 0x7FC00000)))
    # Matrix fixtures can overlap byte 7 only in none of the cases above.
    t.args(r3=bound, r4=matrix if enabled else 0)
