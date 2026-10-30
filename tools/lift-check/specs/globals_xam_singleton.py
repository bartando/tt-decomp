"""Read the shared init guard and return the original singleton address on both branches."""
from liftcheck.spec import *

FUNCTION = "xam_GetInitSingleton"
ADDRESS = 0x82238D60
SOURCE = "src/xam/static_init.c"
CALLS = {0x8242F7D0: stub(ret=0, args=("r3",))}


def inputs(t):
    t.w32(0x8271B2A0, t.pick([0, 1, 2, 3, 0xFFFFFFFF, t.u32()]))
    for off in range(0, 24, 4):
        t.w32(0x8271A860 + off, t.u32())
    t.args()
