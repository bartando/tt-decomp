"""Pixel constants: always registers 0..19 whatever r4/r6 say, from aligned,
unaligned and overlapping sources."""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetPixelShaderConstantF"
ADDRESS = 0x82356A70
SOURCE = "src/graphics/grc_device.cpp"
RET = None


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3010, "device") + rng.choice([0, 0, 0, 4, 8, 12])
    src = t.alloc(16 * 20 + 32, "constants") + rng.randrange(16)
    if rng.randrange(4) == 0:
        src = dev + 0x1780 + rng.choice([-16, -1, 1, 15, 16, 64])
    t.w64(dev + 0x18, rng.choice([0, t.rng.getrandbits(64)]))
    t.args(r3=dev, r4=rng.choice([0, t.u32()]), r5=src, r6=rng.choice([20, t.u32()]))
