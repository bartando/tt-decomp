"""0x8228D1D0: transform bound+0x30 xyz by the instance's forward matrix.

Nonzero centroids/translations, nonsymmetric and non-orthonormal bases,
arbitrary ignored w lanes, output aliasing either input, subnormals/nonfinites.
No ignored bytes, FTOL=0; the checker equates NaNs and signed zeros.
VMX rounding/flush is the emulator's model, not console evidence.
"""
from liftcheck.spec import *

FUNCTION = "rage::phBound_TransformCentroid"
ADDRESS = 0x8228D1D0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    bound = t.alloc(96, "boundAndGuards")
    matrix = t.alloc(96, "matrixAndGuards") + 16
    t.floats(bound, 24, -100, 100)
    t.floats(matrix, 16, -10, 10)
    if rng.randrange(4) == 0:
        t.w32(rng.choice((bound + 48, matrix)) + 4 * rng.randrange(4),
              rng.choice((0, 0x80000000, 1, 0x807FFFFF, 0x00800000,
                          0x7F800000, 0xFF800000, 0x7FC00000)))
    kind = rng.randrange(8)
    if kind < 3:
        for lane in range(3):
            t.wf32(bound + 48 + lane * 4, 0)
        for lane in range(16):
            t.wf32(matrix + lane * 4, 0)
        if kind == 0:
            t.w32(bound + 48, 0x007FFFFF)
            t.wf32(matrix, 1e38)
        elif kind == 1:
            t.wf32(bound + 48, 1e-20)
            t.wf32(matrix, 1e-20)
        else:
            for axis, value in enumerate((1e10, 1., -1e10)):
                t.wf32(bound + 48 + axis * 4, value)
                t.wf32(matrix + axis * 16, 1)
    out = rng.choice((t.alloc(48, "outAndGuards") + 16,
                      bound + 48, bound, matrix, matrix + 48))
    t.args(r3=bound, r4=matrix, r5=out)
