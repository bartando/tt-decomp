"""SWF rotation matrix: angle in f1, including an angle sourced from out.

The ABI passes the angle by value, so an output/input pointer alias cannot reach
this function. Half the trials initialize an output slot with the exact angle
passed in f1, as a caller loading its angle from the destination would do.
"""
from liftcheck.spec import *
import math
import struct

FUNCTION = "rage::swfMakeRotationMatrix"
ADDRESS = 0x823FA2A0
SOURCE = "src/rage/math/swf_matrix.cpp"
FP_CONTRACT = "off"
RET = None


def trig(fn):
    return model(lambda c: c.ret(f1=fn(c.f(1)) if math.isfinite(c.f(1)) else float('nan')),
                 args=("f1",))


CALLS = {0x824302B0: trig(math.cos), 0x824301D8: trig(math.sin)}


def inputs(t):
    rng = t.rng
    out = t.alloc(24, "out")
    t.floats(out, 6)
    angle = rng.choice([0.0, -0.0, 90.0, -180.0, 360.0, rng.uniform(-10000, 10000)])
    angle = struct.unpack('>f', struct.pack('>f', angle))[0]
    if rng.randrange(2) == 0:
        t.wf32(out + 4 * rng.randrange(6), angle)
    t.args(r3=out, f1=angle)
