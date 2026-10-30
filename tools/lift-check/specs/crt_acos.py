"""CRT acos entry thunk into the shared asin/acos core (the core is a stub).

Inputs span [-1, 1], its edges, just outside it, and special values.
"""
from liftcheck.spec import *

FUNCTION = "crt_acos"
ADDRESS = 0x82430E90
SOURCE = "src/rage/math/ph_math.cpp"
CALLS = {0x82430BA8: stub(args=("r4", "f1"))}  # selector and x; result passes through


def inputs(t):
    rng = t.rng
    x = rng.choice([rng.uniform(-1, 1), -1.0, 1.0, 0.0, -0.0, 0.5, 1.0000001, -1.5,
                    float("inf"), float("nan")])
    t.args(f1=x)
