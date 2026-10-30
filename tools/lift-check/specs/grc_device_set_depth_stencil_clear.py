"""0x8235D700: D24S8/float24 clear packing and dirty GPU state.

Exact memory comparison: both format modes, exponent/rounding boundaries,
signed zero, subnormals, negative/large/nonfinite depths, arbitrary stencil
words, equal/unequal cached stencil and both blend bits. Random device guards
and prior 64-bit dirty flags remain observable. No calls, tolerance or ignores.
PPC fctidz saturation/low-word and six-bit variable-shift semantics are covered.
"""
import struct
from liftcheck.spec import *

FUNCTION = "grcDevice_SetDepthStencilClear"
ADDRESS = 0x8235D700
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3000, "device")
    floating = t.index % 2
    t.w16(device + 11464, (rng.getrandbits(16) & ~1) | floating)
    patterns = [0, 0x80000000, 1, 0x7FFFFF, 0x00800000,
                0x30000000, 0x307FFFFF, 0x30800000, 0x37FFFFFC,
                0x387FFFFF, 0x38800000, 0x38800003, 0x38800004,
                0x3F000000, 0x3F7FFFFF, 0x3F800000, 0xBF800000,
                0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC12345]
    bits = patterns[(t.index // 2) % len(patterns)] if t.index % 4 < 2 else rng.getrandbits(32)
    depth = struct.unpack(">f", struct.pack(">I", bits))[0]
    cached = rng.randrange(256)
    stencil = rng.choice([cached, cached, 0, 0xFF, rng.getrandbits(32)])
    t.w8(device + 11650, cached)
    t.args(r3=device, r4=rng.getrandbits(32), r5=rng.getrandbits(32), r6=stencil, f1=depth)
