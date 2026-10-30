"""CRT floor: compare results with the original for ordinary and exceptional doubles.

lift-check compares NaNs as NaNs and treats signed zeros as equal, so their
payloads and result signs are not verified by its floating-point comparison.
"""
from liftcheck.spec import *  # noqa: F401,F403
import math
import struct

FUNCTION = "crt_floor"
ADDRESS = 0x82431910
SOURCE = "src/rage/math/ph_math.cpp"
TRIALS = 2000
FTOL = 0
FP_CONTRACT = "off"


def from_bits(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def inputs(t):
    rng = t.rng
    boundary = rng.choice([0.0, 1.0, 2.0, 1e18, 2.0**53, 2.0**63])
    x = rng.choice([
        0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 1.5, -1.5,
        boundary, math.nextafter(boundary, 0.0), math.nextafter(boundary, math.inf),
        rng.randint(-1000000, 1000000), rng.randint(-1000000, 1000000) + 0.5,
        rng.uniform(-1e6, 1e6), from_bits(rng.getrandbits(64)),
        from_bits(1), from_bits((1 << 52) - 1),
        math.inf, -math.inf, from_bits(0x7ff8000000000123),
        from_bits(0xfff8000000000123), from_bits(0x7ff0000000000001),
    ])
    if rng.randrange(2):
        x = -x
    t.args(f1=x)
