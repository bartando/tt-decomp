"""CRT sqrt (double): fsqrt."""
from liftcheck.spec import *  # noqa: F401,F403
import math

FUNCTION = "crt_sqrt"
ADDRESS = 0x824301D0
SOURCE = "src/rage/math/ph_math.cpp"


def inputs(t):
    rng = t.rng
    t.args(f1=rng.choice([0.0, -0.0, 1.0, 2.0, rng.uniform(0, 1e6), rng.uniform(0, 1e-300), math.inf]))
