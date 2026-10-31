"""Retail double remainder: signed zero, gradual underflow, exact multiples,
wide exponent gaps, random significands and all infinity/NaN/zero cases.
The integer reduction executes on both sides; no libm boundary model or tolerance.
"""
import math
import struct
from liftcheck.spec import *

FUNCTION = "crt_fmod"
ADDRESS = 0x82431D78
SOURCE = "src/crt/fmod.cpp"
TRIALS = 1000
# The symbol map incorrectly splits this leaf at its internal compare block.
EXTRA_RANGES = [(0x82431EA0, 0x82431EFC)]


def inputs(t):
    r = t.rng
    def bits(n):
        return struct.unpack('>d', n.to_bytes(8, 'big'))[0]
    edges = [0.0, -0.0, 1.0, -1.0, 2.0, -2.0, math.inf, -math.inf,
             bits(0x7FF8000012345678), bits(0xFFF0000012345678),
             bits(1), bits(0x8000000000000001), bits(0xFFFFFFFFFFFFF),
             bits(0x10000000000000), bits(0x7FEFFFFFFFFFFFFF)]
    x = r.choice(edges) if r.randrange(2) else bits(r.getrandbits(64))
    y = r.choice(edges) if r.randrange(2) else bits(r.getrandbits(64))
    if r.randrange(5) == 0:
        x, y = r.choice([(x, x), (360.0, 90.0), (-360.0, 90.0),
                          (math.ldexp(1.0, 900), bits(3))])
    t.args(f1=x, f2=y)
