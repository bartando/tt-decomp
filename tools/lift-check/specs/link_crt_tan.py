"""CRT tan: reduction, polynomial and exception dispatch, with scripted FPSCR control.

Exception and quiet-NaN helpers are stubbed: their arguments and returned values
are checked, but their internal FPSCR, errno and matherr effects are not.
The comparison treats NaNs and signed zeros as equal.
"""
from liftcheck.spec import *  # noqa: F401,F403
import math
import struct

FUNCTION = "crt_tan"
ADDRESS = 0x82432628
SOURCE = "src/rage/math/ph_math.cpp"
FP_CONTRACT = "off"
TRIALS = 2000
_control = 0xF8
CALLS = {
    "_fp_set_fpscr_bits": stub(ret=lambda ctx: _control),
    "crt_fp_classify": run(),
    "crt_fp_adjust_exponent": run(),
    "crt_fp_round": run(),
    "crt_fp_quiet_nan": stub(args=("r3", "r5", "f1")),
    "crt_fp_exception": stub(args=("r3", "r4", "r7", "f1", "f2")),
}
CALLS["crt_fp_adjust_exponent"].args = ("r4", "f1")


def bits(n):
    return struct.unpack(">d", struct.pack(">Q", n))[0]


def inputs(t):
    global _control
    rng = t.rng
    _control = rng.choice([0xF8, 0xF0, 0, 8, 0x12345678])
    boundary = rng.choice([0.0, 2**-1022, float.fromhex("0x1.6a09e667f3bcdp-27"),
                           float.fromhex("0x1.1c5831add62e4p+28"), rng.randrange(1, 100) * math.pi / 2])
    x = rng.choice([boundary, math.nextafter(boundary, 0), math.nextafter(boundary, math.inf),
                    rng.uniform(-2, 2), rng.uniform(-1e8, 1e8), rng.uniform(-1e10, 1e10),
                    bits(rng.randrange(1, 1 << 52)), bits(1), bits((1 << 52) - 1),
                    0.0, -0.0, math.inf, -math.inf, bits(0x7ff8000000000123),
                    bits(0x7ff0000000000001), bits(rng.getrandbits(64))])
    t.args(f1=-x if rng.randrange(2) else x)
