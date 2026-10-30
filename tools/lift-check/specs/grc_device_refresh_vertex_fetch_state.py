"""Vertex fetch descriptor refresh and dirty-state propagation.

Limits: declaration counts are bounded to 1..16 (the stored value is count - 1)
so every descriptor and buffer stays in allocated memory. The null declaration
case skips the loop. No writes or bits are ignored; arithmetic inputs include
wraparound and both matching and differing cached state pairs.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_RefreshVertexFetchState"
ADDRESS = 0x82362980
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3500, "device")
    declaration = t.alloc(0x20, "declaration")
    mode = rng.randrange(7)
    count = rng.choice((1, 2, 3, 6, 15, 16))
    t.w32(device + 0x2C90, 0 if mode == 0 else declaration)
    t.w32(declaration + 12, count - 1)
    for i in range(count):
        buffer = t.alloc(0x20, f"buffer_{i}")
        t.w32(device + 0x310C + i * 8, rng.choice((0, 1, 0xFFFFFFFF, rng.getrandbits(32))))
        t.w32(device + 0x3110 + i * 8, 0 if mode == 1 or rng.randrange(4) == 0 else buffer)
        t.w32(buffer + 12, rng.choice((0, 0xFFFFFFFF, 0x1FFFFFFF, rng.getrandbits(32))))
        t.w32(buffer + 16, rng.choice((0, 0xFFFFFFFF, rng.getrandbits(32))))
    for i in range(2):
        value = rng.getrandbits(64)
        t.w64(device + 0x2CA0 + i * 8, value)
        t.w64(device + 0x3190 + i * 8, value ^ (1 << rng.randrange(64)) if mode == 5 or mode == 3 + i else value)
    t.args(r3=device)
