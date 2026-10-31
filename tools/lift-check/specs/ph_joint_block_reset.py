"""0x82154628: signed record count, xyz defaults, flags and common parameters.

Only three undefined scratch W words per active record are ignored; the lift
preserves those words. Every other field, flags, count and guard is compared.
"""
from liftcheck.spec import *
FUNCTION = 'util_4628'
ADDRESS = 0x82154628
SOURCE = 'src/physics/ph_update_object.cpp'
TRIALS = 400


def inputs(t):
    obj = t.alloc(0x260, 'blockAndGuards') + 16
    count = t.rng.choice((-32768, -1, 0, 1, 3, 8))
    t.w16(obj + 0x210, count)
    for i in range(max(0, count)):
        for offset in (12, 28, 44):
            t.ignore(obj + i * 64 + offset, 4)
    t.args(r3=obj, r4=t.rng.getrandbits(32))
