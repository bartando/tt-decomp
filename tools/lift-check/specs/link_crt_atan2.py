"""CRT atan2(y, x) (double): octant folding and the rational approximation; exact."""
from liftcheck.spec import *  # noqa: F401,F403
import math

FUNCTION = "crt_atan2"
ADDRESS = 0x82430FE0
SOURCE = "src/rage/math/ph_math.cpp"


def val(rng):
    return rng.choice([
        0.0, -0.0, 1.0, -1.0, rng.uniform(-2, 2), rng.uniform(-1000, 1000), 1e-300, -1e300,
        math.inf, -math.inf, math.sqrt(3), 2 - math.sqrt(3), rng.uniform(-1e-5, 1e-5),
    ])


def inputs(t):
    rng = t.rng
    y, x = val(rng), val(rng)
    if rng.random() < 0.3:   # ratios around the octant thresholds
        x = rng.uniform(0.1, 10) * rng.choice([1, -1])
        y = x * rng.choice([2 - math.sqrt(3), math.sqrt(3), 1.0]) * (1 + rng.uniform(-1e-12, 1e-12))
    t.args(f1=y, f2=x)
