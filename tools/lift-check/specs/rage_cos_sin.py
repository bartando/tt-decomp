"""0x820D04F0: cos then sin, one double angle, two float outputs.

Execute both CRT callees; check their order, full double arguments, output
rounding and write order (including aliased outputs), plus surrounding guards.
FTOL=0; no ignored bytes. Finite angles include doubles not representable as
float, signed zero, tiny values and argument-reduction boundaries. FP exception
flags/traps and non-finite CRT exception handling are outside this spec.
"""
import math
from liftcheck.spec import *

FUNCTION = "rage::cosSin"
ADDRESS = 0x820D04F0
SOURCE = "src/rage/math/ph_math.cpp"
TRIALS = 1200
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def angle(rng):
    return rng.choice((rng.uniform(-10000, 10000), rng.uniform(-8, 8),
                       0., -0., 2.**-140, -2.**-140, 0.12500000000000003,
                       math.pi / 2 + rng.choice((-1, 1)) * 2.**-30,
                       math.pi + 2.**-30, 2.**26 + 0.125))


def inputs(t):
    storage = t.alloc(64, "outputsAndGuards")
    cosine = storage + 16
    sine = cosine + t.rng.choice((0, 4, 16))
    t.wf32(cosine, 123.)
    t.wf32(sine, -456.)
    t.args(r3=cosine, r4=sine, f1=angle(t.rng))
