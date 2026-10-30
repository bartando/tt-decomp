"""Sampler LOD bias: float bits in r5, scaled to fetch dword 4's lod_bias field.

Biases cover the normal -16..16 range plus fractions, huge values, infinities and
NaNs to pin down fctidz saturation. The scale constant is patched to random
floats too, and samplers past 63 check the srd dirty-bit wrap.
"""
import struct

from liftcheck.spec import *

FUNCTION = "grcDevice_setSamplerLodBias"
ADDRESS = 0x82355948
SOURCE = "src/graphics/grc_device.cpp"


def f32(x):
    return struct.unpack(">I", struct.pack(">f", x))[0]


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3800, "device")
    sampler = rng.choice([rng.randrange(26), 0, 25, 31, 32, 63, 64, 65, 127, 128, 129, 255])
    t.w32(device + (sampler + 48) * 24 + 16, t.u32())
    t.w64(device + 32, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    if rng.random() < 0.3:
        t.w32(0x82079AF0, rng.choice([t.u32(), f32(rng.uniform(-100, 100))]))
    bias = rng.choice([
        f32(rng.uniform(-16, 16)), f32(rng.uniform(-1, 1)), f32(rng.randrange(-20, 20) / 32),
        f32(1e20), f32(-1e20), 0x7F800000, 0xFF800000, 0x7FC00000, 0xFFC00001, 0x80000000, t.u32(),
    ])
    t.args(r3=device, r4=sampler, r5=bias)
