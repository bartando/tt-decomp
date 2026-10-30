"""0x8223F840: exact clamped/truncated RGBA -> 0xAARRGGBB.

All float32 encodings are valid, including sNaNs, infinities, signed zeros,
and subnormals. NaNs survive the original clamp, then convert to a zero byte.
Inputs include every channel-byte boundary and output aliasing every lane.
Compare packed bytes and returned pointer exactly; FP status/traps are outside
scope. Constants retain their image values (0, 1, 255).
"""
import struct
from liftcheck.spec import *

FUNCTION = "PackClampedColorARGB8"
ADDRESS = 0x8223F840
SOURCE = "src/graphics/fx_effects.cpp"
TRIALS = 1200
FTOL = 0
FP_CONTRACT = "off"

EDGES = (0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
         0x3F000000, 0x3F7FFFFF, 0x3F800000, 0x3F800001, 0xBF800000,
         0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
         0x7FC12345, 0xFFC12345, 0x7F812345, 0xFF812345)


def inputs(t):
    color = t.alloc(48, "rgbaAndGuards") + 16
    separate = t.alloc(16, "packedAndGuards") + 4
    # Cycle overlaps deterministically, including all four input components.
    out = separate if t.index % 5 == 0 else color + 4 * (t.index % 5 - 1)
    for lane in range(4):
        if t.index < 4 * len(EDGES):
            bits = EDGES[t.index // 4] if lane == t.index % 4 else (0x3E800000 + lane * 0x00800000)
        elif t.index < 4 * len(EDGES) + 768:
            n = t.index - 4 * len(EDGES)
            boundary = struct.unpack(">I", struct.pack(">f", (n // 3) / 255.0))[0]
            bits = boundary + (n % 3 - 1) if boundary else n % 3
            if lane != n % 4:
                bits = t.u32()
        else:
            bits = t.u32()
        t.w32(color + lane * 4, bits)
    t.args(r3=out, r4=color)
