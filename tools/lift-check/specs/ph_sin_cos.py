"""0x820D04F0 shared by the Z rotation: rounded cos then sin of one double.

Run the real CRT callees, checking their double arguments and both outputs,
including aliased outputs (the sine store wins), signed zero and guards.
"""
import math
from liftcheck.spec import *

FUNCTION = "ph_SinCos"
ADDRESS = 0x820D04F0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    storage = t.alloc(64, "outputsAndGuards")
    c = storage + 16
    s = c if t.index % 3 == 0 else storage + 32
    angle = t.rng.choice((0., -0., math.pi / 2, 1 + 2**-30,
                          t.rng.uniform(-10000, 10000)))
    t.args(r3=c, r4=s, f1=angle)
