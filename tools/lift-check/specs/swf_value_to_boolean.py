"""Exercise all tags and payload bit patterns, including signed zero and NaNs."""
from liftcheck.spec import *

FUNCTION = "swfValueToBoolean"
ADDRESS = 0x823FA420
SOURCE = "src/rage/swf_vm.cpp"
TRIALS = 1000


def inputs(t):
    r = t.rng
    value = t.alloc(8, 'value')
    tag = r.choice([0, 1, 2, 3, 4, 5, 6, 0xffffffff, r.getrandbits(32)])
    payload = r.choice([0, 1, 0x1000000, 0x10000, 0x80000000, 0x3f800000,
                        0x7f800000, 0x7fc00000, r.getrandbits(32)])
    t.w32(value, payload)
    t.w32(value + 4, tag)
    t.args(r3=value)
