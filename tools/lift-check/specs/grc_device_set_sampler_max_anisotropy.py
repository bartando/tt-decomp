"""Sampler maximum anisotropy, including inactive walks and dirty-bit boundaries.

Active walks index the 17-entry table, so their anisotropy is 0..16. Inactive
walks also exercise arbitrary values, which are cached as a byte without a table
read. Random fetch words, dirty masks, and patched table values expose bit masks.
No calls or memory are ignored; this checks shadow state rather than GPU output.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_setSamplerMaxAnisotropy"
ADDRESS = 0x82355828
SOURCE = "src/graphics/grc_device.cpp"


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3800, "device")
    sampler = rng.choice([rng.randrange(26), 0, 25, 31, 32, 63, 64, 65, 127, 128, 129, 255])
    fetch = device + (sampler + 48) * 24
    walks = rng.choice([0, 0x400, 0x800, 0xC00])
    t.w32(fetch + 16, (t.u32() & ~0xC00) | walks)
    anisotropy = rng.randrange(17) if walks else rng.choice([rng.randrange(17), 255, 256, t.u32()])
    t.w64(device + 32, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    for i in range(17):
        t.w32(0x82065D10 + 4 * i, t.u32())
    t.args(r3=device, r4=sampler, r5=anisotropy)
