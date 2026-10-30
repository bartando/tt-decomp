"""Shared CRT asin/acos core: exact result and helper-call comparison.

Limits: selectors are 0/1, the only values supplied by the two entry thunks.
Classification, exponent adjustment and sqrt execute their original PPC.
FPSCR save/restore returns scripted control words (including inexact enabled
and disabled); its arguments and the resulting exception dispatch are checked,
but hardware FPSCR state, traps, errno and matherr inside the exception/quiet-NaN
helpers are outside this single-function test. Those two helpers return seeded
random doubles, so their return propagation is checked independently of libm.
NaN payload/quieting and signed-zero result bits follow lift-check's float
comparison limits; signed-zero inputs still exercise the distinct control flow.
"""
from liftcheck.spec import *  # noqa: F401,F403
import math
import struct

FUNCTION = "crt_asin_acos"
ADDRESS = 0x82430BA8
SOURCE = "src/rage/math/ph_math.cpp"
TRIALS = 2000
FTOL = 0

_control = 0xF8
CALLS = {
    "_fp_set_fpscr_bits": stub(ret=lambda ctx: _control),
    "crt_fp_classify": run(),
    "crt_fp_adjust_exponent": run(),
    "crt_fp_sqrt": run(),
    "crt_fp_quiet_nan": stub(args=("r3", "r5", "f1")),
    "crt_fp_exception": stub(args=("r3", "r4", "r7", "f1", "f2")),
}
# The helper reads delta in r4 and value in f1; its r3 slot is unused.
CALLS["crt_fp_adjust_exponent"].args = ("r4", "f1")


def from_bits(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def inputs(t):
    global _control
    rng = t.rng
    _control = rng.choice([0xF8, 0xF0, 0, 8, 0x12345678])
    tiny = float.fromhex("0x1.6a09e667f3bcdp-27")
    boundary = rng.choice([0.0, tiny, 0.5, 1.0, float.fromhex("0x1p-1022")])
    x = rng.choice([
        0.0, -0.0, 1.0, -1.0, 0.5, -0.5,
        boundary, math.nextafter(boundary, 0.0), math.nextafter(boundary, math.inf),
        rng.uniform(0.0, 0.5), rng.uniform(0.5, 1.0), rng.uniform(1.0, 1e4),
        math.ldexp(rng.uniform(0.5, 1), rng.randrange(-1073, -26)),
        from_bits(rng.randrange(1, 1 << 52)),  # subnormals, including mantissa-high != 0
        from_bits(1), from_bits((1 << 52) - 1),
        math.inf, -math.inf,
        from_bits(0x7FF8000000000123), from_bits(0xFFF8000000000123),
        from_bits(0x7FF0000000000001), from_bits(0xFFF0000000000001),
        from_bits(rng.getrandbits(64)),
    ])
    if rng.randrange(2):
        x = -x
    t.args(f1=x, r4=rng.randrange(2))
