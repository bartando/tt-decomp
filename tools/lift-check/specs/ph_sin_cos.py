"""0x820D04F0: one double angle, rounded cosine/sine outputs in that order.

Supporting check for mat33FromEuler's corrected shared helper. Original CRT
callees execute; exact output and call comparison, including aliased outputs,
negative zero and angles that cannot be represented by float32. Finite inputs,
default FP rounding, no tolerance or ignored writes.
"""
from liftcheck.spec import *

FUNCTION = "ph_SinCos"
ADDRESS = 0x820D04F0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1000
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    rng = t.rng
    outputs = t.alloc(32, "outputsAndGuards")
    t.args(r3=outputs + 8, r4=outputs + (8 if t.index % 3 == 0 else 16),
           f1=rng.choice([0.0, -0.0, 0.12500000000000003, rng.uniform(-100, 100)]))
