from liftcheck.spec import *
from specs._crt_fp_inputs import value
FUNCTION = "crt_fp_adjust_exponent"
ADDRESS = 0x82435770
SOURCE = "src/crt/fp_helpers.cpp"
TRIALS = 1000

def inputs(t):
    delta = [-0x80000000, -4097, -2048, -1536, -1, 0, 1, 1536, 2048,
             4096, 0x7FFFFFFF][t.index % 11] if t.index < 200 else t.rng.randrange(-2**31, 2**31)
    t.args(r3=t.rng.getrandbits(32), r4=delta, f1=value(t))
