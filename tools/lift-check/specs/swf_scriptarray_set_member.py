"""Array slot 11 converts a key to signed index, writes two words or returns 0.

Execute original integer conversion. Include zero length, bounds, signed indices,
boolean/nonnumeric tags, and value/destination aliasing. Negative indices have
allocated prefix storage: retail checks only the upper bound, not index >= 0.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfSCRIPTARRAY::SetMember"
ADDRESS = 0x823FEC38
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = "r3"
CALLS = {0x823FA5C8: run()}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x18, "array")
    storage = t.alloc(8 * 16, "elements")
    elements = storage + 8 * 4
    count = rng.choice((0, 1, 2, 8))
    t.w32(obj + 0x10, elements)
    t.w16(obj + 0x14, count)
    key = t.alloc(8, "key")
    tag = rng.choice((2, 3, 4, 5, 6, 7, 0xFFFFFFFF))
    t.w32(key + 4, tag)
    t.w32(key, rng.choice((0, 1, count, max(0, count - 1), 0x7FFFFFFF, 0xFFFFFFFF, 0xFFFFFFFE)))
    value = rng.choice((t.alloc(8, "value"), elements, elements + 4))
    t.args(r3=obj, r4=key, r5=value)
