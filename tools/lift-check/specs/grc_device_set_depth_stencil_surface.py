"""Depth surface bind: reference swap, depth registers, cached-target match bit.

Covers binding and unbinding, rebinding the same surface (release before
acquire), reference counts on both sides of the release condition, colour
targets bound or not (grc_36E8 sizing), and every match/mismatch pattern of the
five bound surfaces against the cached set.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetDepthStencilSurface"
ADDRESS = 0x823565F8
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {
    0x82352708: stub(ret="void", args=("r3",)),
    0x823536E8: stub(ret="void", args=("r3", "r4")),
}
RET = None
TRIALS = 1000


def surface(t, name):
    rng = t.rng
    buf = t.alloc(0x40, name)
    for k in range(16):
        t.w32(buf + 4 * k, t.u32())
    t.w32(buf, rng.choice([0x80000, 0x100000, 0x80000 | rng.choice([0, 1, 0x100, 0x10000]), t.u32()]))
    return buf


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3400, "device")
    for off in (10396, 0x2CC8, 0x2D74, 0x2D80, 0x2EC4, 0x2EC8):
        t.w32(dev + off, t.u32())
    for off in (0x20, 0x28, 0x30):
        t.w64(dev + off, rng.choice([0, rng.getrandbits(64)]))
    t.w8(dev + 0x28C0, rng.randrange(256))
    t.w8(dev + 0x28C2, rng.randrange(256))
    t.w32(dev + 0x32A0, rng.choice([0, 0, 0, t.u32()]))
    old = rng.choice([0, surface(t, "previous")])
    new = rng.choice([0, surface(t, "surface"), old])
    # Colour targets and the cached set: equal, null, or different per slot.
    for i in range(4):
        bound = rng.choice([0, t.u32(), t.u32()])
        t.w32(dev + 0x30F8 + i * 4, bound)
        t.w32(dev + 0x32B0 + i * 4, rng.choice([bound, bound, t.u32()]))
    t.w32(dev + 0x3108, old)
    t.w32(dev + 0x32C0, rng.choice([new, new, t.u32()]))
    t.args(r3=dev, r4=new)
