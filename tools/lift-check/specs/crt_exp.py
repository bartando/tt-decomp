"""0x82432478: rational exponential, exponent halfword scaling and inclusive clamps.

Exact doubles and no tolerance. Covers both cutoffs and adjacent doubles,
integer reduction ties, exponent -1's skip path, overflow conversion inputs,
signed zero, infinities, NaNs and mutable overflow replacement data.
"""
import math
from liftcheck.spec import *
FUNCTION = 'crt_exp'
ADDRESS = 0x82432478
SOURCE = 'src/crt/exp.cpp'
TRIALS = 1200
FP_CONTRACT = 'off'


def inputs(t):
    hi, lo = float.fromhex('0x1.62e42fefa39f8p+9'), -float.fromhex('0x1.6232bdd7abcdap+9')
    values = (0., -0., 1., -1., .1, -.1, hi, math.nextafter(hi, -math.inf),
              math.nextafter(hi, math.inf), lo, math.nextafter(lo, -math.inf),
              math.nextafter(lo, math.inf), 1e300, -1e300, math.inf, -math.inf,
              math.nan, 2**-1074, -2**-1074, 2**63, -2**63)
    if t.index % 4 == 0:
        x = t.rng.uniform(-710, 710)
    elif t.index % 4 == 1:
        x = t.pick((-1023, -1022, -2, -1, 0, 1, 2, 1022, 1023)) + .5
        x /= float.fromhex('0x1.71547652b8ecbp+0')
    else:
        x = values[t.index % len(values)]
    replacement = 123. if x == hi else t.pick((math.inf, 123., -math.inf, math.nan))
    t.wf64(0x825B12A8, replacement)
    t.args(f1=x)
