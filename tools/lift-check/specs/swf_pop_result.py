"""Support lift for Invoke: pop both value words, update depth and return dst.

Empty pops log and materialize {0,3} at stack[0]. Valid nonempty depths are
bounded to eight entries; destination may alias a stack entry. Random guards,
stack, result, depth, call arguments and returned pointer compare exactly.
"""
from liftcheck.spec import *

FUNCTION = "swfPopResult"
ADDRESS = 0x82403270
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = "r3"
EXTERNS = {"rage_DebugLog": 0x8240E6D0,
           "rage::g_swfCallDepth": 0x82604D1C,
           "rage::g_swfValueStack": 0x82715C98}
CALLS = {0x8240E6D0: stub(ret="void", args=("r3",))}


def inputs(t):
    depth = t.index % 9
    t.w32(0x82604D1C, depth)
    for i in range(9):
        t.w32(0x82715C98 + 8 * i, t.u32())
        t.w32(0x82715C98 + 8 * i + 4, t.u32())
    out = t.alloc(16, "poppedResultAndGuards") + 4
    if t.index % 4 == 0:
        out = 0x82715C98 + 8 * t.rng.randrange(8)
    t.args(r3=out)
