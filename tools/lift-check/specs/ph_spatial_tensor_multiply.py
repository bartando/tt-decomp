"""0x822556E0: coupled 3x3 blocks, staged aliased loads/stores, shuffled W."""
from liftcheck.spec import *
FUNCTION = 'phSpatialTensor_Multiply'
ADDRESS = 0x822556E0
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 800
FP_CONTRACT = 'off'
FTOL = 1e-99


def inputs(t):
    matrix = t.alloc(224, 'matrixAndGuards') + 16
    value = t.alloc(80, 'inputAndGuards') + 16
    out = t.alloc(64, 'outputAndGuards') + 16
    t.floats(matrix, 48, -10, 10)
    t.floats(value, 12, -10, 10)
    t.floats(out, 8, -10, 10)
    if t.index % 3 == 0:
        out = t.rng.choice((matrix, matrix + 64, matrix + 128, value, value + 16))
    if t.index % 5 == 0:
        t.w32(t.rng.choice((matrix, value)) + 4 * t.rng.randrange(8),
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.args(r3=matrix, r4=value, r5=out)
