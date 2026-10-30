"""Texture bind: fetch-constant merge, mip clamps, dirty bit, reference swap.

Slots 0..31 (the srd shift wraps differently from the lift only at 128+). Covers
binding with and without a previously bound texture, null binds, rebinding the
same texture, addresses on both sides of the 4KB-aperture fix-up, and reference
counts that do and don't reach the release condition.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetTexture"
ADDRESS = 0x82359940
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {0x82352708: stub(ret="void", args=("r3",))}
RET = None


def texture(t, name):
    rng = t.rng
    tex = t.alloc(0x40, name)
    for k in range(0x40 // 4):
        t.w32(tex + 4 * k, t.u32())
    refs = rng.choice([0x80000, 0x100000, 0x80000 | rng.choice([0, 1, 0x10000]), t.u32()])
    t.w32(tex, refs)
    for word in (5, 9):
        t.w32(tex + 4 * word, rng.choice([t.u32(), 0x1DFFF000, 0x1E000000, 0x00100000]))
    return tex


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3200, "device")
    slot = rng.randrange(32)
    for offset in range((slot + 48) * 24, (slot + 48) * 24 + 24, 4):
        t.w32(dev + offset, t.u32())
    t.w32(dev + 0x20, t.u32())
    t.w32(dev + 0x24, t.u32())
    t.w32(dev + 10396, t.u32())
    t.w8(dev + 12046 + slot, rng.randrange(16))
    t.w8(dev + 12072 + slot, rng.randrange(16))
    old = rng.choice([0, texture(t, "previous")])
    t.w32(dev + (slot + 3176) * 4, old)
    new = rng.choice([0, texture(t, "texture"), old])
    t.args(r3=dev, r4=slot, r5=new)
