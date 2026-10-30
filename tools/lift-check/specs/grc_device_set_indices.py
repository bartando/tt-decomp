"""Index buffer bind at device+0x30F4: reference swap and fence stamp.

Covers binding with and without a previous buffer, null binds, rebinding the
same buffer (increment before decrement) and reference counts on both sides of
the release condition.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetIndices"
ADDRESS = 0x82356210
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {0x82352708: stub(ret="void", args=("r3",))}
RET = None
TRIALS = 1000


def index_buffer(t, name):
    rng = t.rng
    buf = t.alloc(0x10, name)
    for k in range(4):
        t.w32(buf + 4 * k, t.u32())
    refs = rng.choice([0x80000, 0x100000, 0x80000 | rng.choice([0, 1, 0x100, 0x10000]), t.u32()])
    t.w32(buf, refs)
    return buf


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3200, "device")
    t.w32(dev + 10396, t.u32())
    old = rng.choice([0, index_buffer(t, "previous")])
    t.w32(dev + 0x30F4, old)
    new = rng.choice([0, index_buffer(t, "indices"), old])
    t.args(r3=dev, r4=new)
