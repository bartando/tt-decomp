"""Vertex stream bind: reference swap, dirty bit, offset/stride bookkeeping.

Covers binding with and without a previously bound buffer, null binds, rebinding
the same buffer (increment before decrement), reference counts on both sides of
the release condition, and strides that aren't multiples of four.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetStreamSource"
ADDRESS = 0x82356118
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {0x82352708: stub(ret="void", args=("r3",))}
RET = None


def vertex_buffer(t, name):
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
    stream = rng.randrange(16)
    t.w64(dev + 0x30, rng.choice([0, rng.getrandbits(64)]))
    t.w32(dev + 10396, t.u32())
    t.w32(dev + 0x310C + stream * 8, t.u32())
    t.w8(dev + 0x3190 + stream, rng.randrange(256))
    old = rng.choice([0, vertex_buffer(t, "previous")])
    t.w32(dev + 0x310C + stream * 8 + 4, old)
    new = rng.choice([0, vertex_buffer(t, "buffer"), old])
    stride = rng.choice([rng.randrange(0, 128, 4), rng.randrange(1024), t.u32()])
    t.args(r3=dev, r4=stream, r5=new, r6=t.u32(), r7=stride)
