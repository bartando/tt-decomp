"""0x820C3F10: one double angle, padded 3x3 X rotation; padding untouched.

Run original CRT sin/cos, compare their double arguments and every output byte.
Includes non-float-representable angles, signed zero and quadrant boundaries.
"""
import math
from liftcheck.spec import *

FUNCTION = "ph_BuildRotationMatrixX"
ADDRESS = 0x820C3F10
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    storage = t.alloc(80, "matrixAndGuards")
    angle = t.rng.choice((0.0, -0.0, math.pi / 2, -math.pi, 2 * math.pi,
                          1 + 2**-30, t.rng.uniform(-10000, 10000)))
    t.args(r3=storage + 16, f1=angle)
