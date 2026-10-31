"""0x8228D0E8: enabled centroid cache reuses the verified output transform.

Includes disabled/null matrix, non-1 enable flags, non-orthonormal matrices,
aliased matrices, ignored W, subnormal/nonfinite inputs, and untouched guards.
Execute the original output variant transparently: the game inlines its body.
"""
from liftcheck.spec import *

FUNCTION = "phBound_TransformWorldCentroid"
ADDRESS = 0x8228D0E8
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
CALLS = {"rage::phBound_TransformCentroid": run(transparent=True)}


def inputs(t):
    rng = t.rng
    bound = t.alloc(0xA0, "boundAndGuards") + 16
    matrix = t.alloc(96, "matrixAndGuards") + 16
    t.floats(bound, 32, -50, 50)
    if t.index % 3 == 0:
        matrix = bound + rng.choice((0, 0x10, 0x20, 0x30, 0x40))
    t.floats(matrix, 16, -10, 10)
    if t.index % 5 == 0:
        t.w32(rng.choice((bound + 48, matrix)) + 4 * rng.randrange(4),
              rng.choice((0, 0x80000000, 1, 0x807FFFFF, 0x00800000,
                          0x7F800000, 0xFF800000, 0x7FC00000)))
    enabled = (0, 1, 2, 255)[t.index % 4]
    t.w8(bound + 6, 0)
    t.w8(bound + 7, enabled)
    t.args(r3=bound, r4=matrix if enabled else 0)
