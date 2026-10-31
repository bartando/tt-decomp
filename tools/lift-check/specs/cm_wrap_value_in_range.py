"""Wrap @0x821129D0 with the real double CRT remainder, preserving the caller's
single-precision subtractions and final rounding. Includes boundaries, inverted
and equal ranges, multiples, huge quotients, signed zeros and unordered inputs.
"""
import struct
from liftcheck.spec import *

FUNCTION = "WrapValueInRange"
ADDRESS = 0x821129D0
SOURCE = "src/game/camera/cm_cam_actions.cpp"
TRIALS = 1000
CALLS = {
    "crt_fmod": run(),
    # The symbol map splits fmod at this internal compare block.
    0x82431EA0: run(transparent=True, args=()),
}


def inputs(t):
    r = t.rng
    lo, hi = r.choice([(-180., 180.), (0., 360.), (-1., 1.), (5., 5.),
                       (10., -10.), (-0., 0.), (-1e-20, 1e-20)])
    value = r.choice([lo, hi, (lo + hi) / 2, lo - 360., hi + 720.,
                      r.uniform(-1e20, 1e20), float('nan'), float('inf'),
                      -float('inf'), -0., 0.])
    def f32(x):
        return struct.unpack(">f", struct.pack(">f", x))[0]
    t.args(f1=f32(value), f2=f32(lo), f3=f32(hi))
