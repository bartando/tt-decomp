"""0x820C3F98: double-angle padded Y rotation, all bytes/calls compared.

Run original CRT sin/cos; cover quadrants, non-float angles, signed zero,
large angles and guards/padding/translation preservation. No tolerance/ignores.
"""
import math
from liftcheck.spec import *

FUNCTION = "ph_BuildRotationMatrixY"
ADDRESS = 0x820C3F98
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    storage = t.alloc(96, "matrixAndGuards")
    angle = (0.0, -0.0, math.pi / 2, -math.pi, 2 * math.pi,
             1 + 2**-30, -1 - 2**-40, t.rng.uniform(-1e6, 1e6))[t.index % 8]
    t.args(r3=storage + 16, f1=angle)
