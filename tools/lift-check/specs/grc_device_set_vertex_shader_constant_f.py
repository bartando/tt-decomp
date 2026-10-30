"""Vertex constants: aligned and unaligned source, group boundaries and empty updates."""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetVertexShaderConstantF"
ADDRESS = 0x82356928
SOURCE = "src/graphics/grc_device.cpp"
RET = None


def inputs(t):
    rng = t.rng
    dev = t.alloc(0x3000, "device")
    first = rng.choice([0, 1, 3, 4, 63, 64, 127, 252, 255, 256, rng.randrange(270)])
    count = rng.choice([0, 1, 2, 3, 4, 5, 7, 8, 16, 20, 64, 255, 256, 260, rng.randrange(30)])
    src = t.alloc(16 * 260 + 32, "constants") + rng.randrange(16)
    if count and rng.randrange(4) == 0:
        src = dev + 0x780 + first * 16 + rng.choice([-16, -1, 0, 1, 16])
    t.w64(dev + 0x10, rng.choice([0, t.rng.getrandbits(64)]))
    t.args(r3=dev, r4=first, r5=src, r6=count)
