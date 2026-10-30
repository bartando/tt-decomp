"""Link the original static node into the image singleton, preserving its existing head."""
from liftcheck.spec import *

FUNCTION = "xam_static_init_0FF0"
ADDRESS = 0x82580FF0
SOURCE = "src/xam/static_init.c"
CALLS = {0x82238D60: returns(0x8271A860)}


def inputs(t):
    t.w32(0x8271A868, t.pick([0, t.alloc(16, "oldHead")]))
    t.w32(0x8271A86C, t.pick([0, 1, 0xFFFFFFFF, t.u32()]))
    t.args()
