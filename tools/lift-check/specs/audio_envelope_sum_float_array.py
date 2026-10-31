"""Existing 0x82172C08 lift: prefix sums and unrolled/scalar cleanup indexing."""
from liftcheck.spec import *

FUNCTION = "rage::phBoundCapsule::SumFloatArray"
ADDRESS = 0x82172C08
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1000
EXTERNS = {"g_floatZero": 0x8202D110}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x150, "duration array")
    for i in range(72):
        value = rng.uniform(-100, 100)
        if t.index % 3 == 0:
            value = [16777216.0, 1.0, -16777216.0, 1.0][i % 4]
        t.wf32(obj + 0x30 + 4 * i, value)
    count = rng.choice([-8, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 31, 32, 63, 64])
    t.args(r3=obj, r4=count)
