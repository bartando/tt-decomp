"""Sampler address mode W: r5's low three bits go to fetch dword 0's clamp field.

Modes include junk high bits to check the mask, and samplers past 63 check the
srd dirty-bit wrap.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_setSamplerAddressW"
ADDRESS = 0x82355BF8
SOURCE = "src/graphics/grc_device.cpp"


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3800, "device")
    sampler = rng.choice([rng.randrange(26), 0, 25, 31, 32, 63, 64, 65, 127, 128, 129, 255])
    t.w32(device + (sampler + 48) * 24, t.u32())
    t.w64(device + 32, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    t.args(r3=device, r4=sampler, r5=rng.choice([0, 1, 2, 7, rng.randrange(16), t.u32()]))
