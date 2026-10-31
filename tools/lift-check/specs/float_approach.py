"""Both directions, crossing/equality, reversed steps, signed zero, NaNs."""
import struct
from liftcheck.spec import *

FUNCTION = "pongPlayer_99B0_g"
ADDRESS = 0x820C99B0
SOURCE = "src/rage/math/float_approach.cpp"
TRIALS = 1000

def float_bits(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]

def inputs(t):
    cases = [
        (0., 1., 2., 1.), (2., 1., 2., 1.), (1., 1., 2., 1.),
        (0., 1., .1, .25), (2., 1., .1, .25),
        (0., 1., -2., 1.), (2., 1., -2., 1.),
        (-0., 0., 0., 1.), (0., -0., 0., 1.),
        (float_bits(0x7FC00042), 1., 1., 1.),
        (1., float_bits(0x7FC00042), 1., 1.),
        (0., 1., float_bits(0x7FC00042), 1.),
        (2., 1., float_bits(0x7FC00042), 1.),
    ]
    if t.index < len(cases):
        current, target, rate, dt = cases[t.index]
    else:
        current, target, rate, dt = [t.rng.uniform(-100, 100) for _ in range(4)]
    value = t.alloc(16, "value")
    t.wf32(value, current)
    target, rate, dt = [struct.unpack(">f", struct.pack(">f", x))[0] for x in (target, rate, dt)]
    t.args(r3=value, f1=target, f2=rate, f3=dt)
