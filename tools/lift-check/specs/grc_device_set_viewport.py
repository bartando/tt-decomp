"""Viewport set: target-size clip, cached target set, transform constants, dirty bits.

Covers no target bound (early out), colour 0 vs depth-only surfaces, the cached
target-size path with matching, null and mismatching slots, viewports inside and
past the target edge (unsigned wrap included), random depth ranges and a patched
scale constant. FP_CONTRACT off: the asm rounds each product before adding.
"""
import struct

from liftcheck.spec import *

FUNCTION = "grcDevice_SetViewport"
ADDRESS = 0x82355ED0
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {0x82355E08: stub(ret="void", args=("r3", "r4"))}
RET = None
FP_CONTRACT = "off"


def f32(x):
    return struct.unpack(">I", struct.pack(">f", x))[0]


def surface(t, name):
    s = t.alloc(0x20, name)
    for k in range(8):
        t.w32(s + 4 * k, t.u32())
    t.w32(s + 0x18, t.rng.choice([t.u32(), (719 << 13) | 1279, 0]))
    return s


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3500, "device")
    color = rng.choice([0, surface(t, "color0"), surface(t, "color0")])
    depth = rng.choice([0, surface(t, "depth")])
    targets = [color, rng.choice([0, t.u32()]), rng.choice([0, t.u32()]), rng.choice([0, t.u32()]), depth]
    for i, v in enumerate(targets):
        t.w32(dev + 0x30F8 + 4 * i, v)
        t.w32(dev + 0x32B0 + 4 * i, rng.choice([v, v, v, t.u32(), 0]))
    t.w8(dev + 0x28C0, t.u32() & 0xFF)
    t.w32(dev + 0x34A8, rng.choice([1280, rng.randrange(1, 4096), t.u32()]))
    t.w32(dev + 0x34AC, rng.choice([720, rng.randrange(1, 4096), t.u32()]))
    t.w64(dev + 0x28, rng.choice([0, rng.getrandbits(64)]))
    if rng.random() < 0.2:
        t.w32(0x8202D10C, rng.choice([t.u32(), f32(rng.uniform(-2, 2))]))
    vp = t.alloc(0x18, "viewport")
    for k in range(4):
        t.w32(vp + 4 * k, rng.choice([rng.randrange(2000), rng.randrange(1 << 24), t.u32()]))
    t.w32(vp + 0x10, rng.choice([f32(0.0), f32(rng.random()), t.u32()]))
    t.w32(vp + 0x14, rng.choice([f32(1.0), f32(rng.random()), t.u32()]))
    t.args(r3=dev, r4=vp)
