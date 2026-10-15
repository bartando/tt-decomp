"""CRT cos (double): two-part reduction by pi and the odd polynomial; exact."""
from liftcheck.spec import *  # noqa: F401,F403
import math

FUNCTION = "crt_cos"
ADDRESS = 0x824302B0
SOURCE = "src/rage/math/ph_math.cpp"


def inputs(t):
    rng = t.rng
    k = rng.randrange(-40, 40)
    x = rng.choice([
        0.0, -0.0, 1e-300, -1e-310, rng.uniform(-4, 4), rng.uniform(-100, 100),
        k * math.pi / 2, k * math.pi / 2 + rng.uniform(-1e-9, 1e-9), rng.uniform(-1e6, 1e6),
        2.2e8, 2.2e8 - 1, -2.2e8 - 1, rng.uniform(-1e9, 1e9), 1e300, math.inf, -math.inf,
    ])
    t.args(f1=x)
