"""Linear/logarithmic/sine fade curves and exact float rounding boundaries.

Libm calls are models, comparing both input doubles and returning their math
results. This validates the lift's dispatch/arithmetic, not the original CRT.
"""
import math
from liftcheck.spec import *

FUNCTION = "rage::xactFade_ApplyCurve"
ADDRESS = 0x82453A98
SOURCE = "src/rage/audio/xact_fade.cpp"
TRIALS = 600
EXTERNS = {"sin": 0x824301D8, "pow": 0x82431308}


def power(c):
    try:
        value = math.pow(c.f(1), c.f(2))
    except OverflowError:
        value = float("inf")
    c.ret(f1=value)


def sine(c):
    value = c.f(1)
    c.ret(f1=math.sin(value) if math.isfinite(value) else float("nan"))


CALLS = {0x82431308: model(power, args=("f1", "f2")),
         0x824301D8: model(sine, args=("f1",))}


def inputs(t):
    rng = t.rng
    fade = t.alloc(24, "fade")
    t.w32(fade + 12, rng.choice((0, 1, 1, 2, 2, 3, 0xffffffff)))
    t.wf32(fade + 20, rng.choice((0.0, -0.0, 0.5, 1.0, -1.0, 40.0, -50.0,
                                 float("inf"), -float("inf"), float("nan"),
                                 rng.uniform(-80, 80), rng.uniform(0, 1))))
    t.args(r3=fade)
