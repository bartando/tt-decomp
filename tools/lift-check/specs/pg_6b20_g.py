"""Staging-vertex tangent write: absent attribute, packed 2:10:10:10 and raw copy.

The mapping helper can replace the staging pointer and the packed flag, which
the original reads only after the call. Exercise address wrap, vector address
rounding, unaligned raw copies and packing boundaries. pg_7578_g is modeled at
the boundary; this checks only pg_6B20_g.
"""
from liftcheck.spec import *

FUNCTION = "pg_6B20_g"
ADDRESS = 0x82156B20
SOURCE = "src/graphics/grc_vertex_buffer.cpp"
FP_CONTRACT = "off"  # VMX multiply/subtract round separately.


def map_buffer(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x18, ctx.read(obj + 0x10, 4))
    ctx.write(obj + 0xD9, ctx.read(obj + 0xDA, 1))
    ctx.write(obj + 0xDB, b"\x01")
    ctx.ret(r3=1)


CALLS = {
    "pg_7578_g": model(map_buffer, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0xE0, "vertexBuffer")
    fmt = t.alloc(4, "format")
    data = t.alloc(512, "staging")
    old_data = t.alloc(512, "oldStaging")
    source = t.alloc(64, "tangent")
    t.floats(source, 16, -2, 2)

    present = rng.random() < 0.85
    t.w32(fmt, (t.u32() & ~0x4000) | (0x4000 if present else 0))
    t.w32(obj + 8, fmt)
    mapped = rng.randrange(2)
    t.w8(obj + 0xDB, mapped)
    packed = rng.choice([0, 0, 1, 255])
    t.w8(obj + 0xD9, packed)
    t.w8(obj + 0xDA, packed if rng.random() < 0.7 else rng.choice([0, 1]))

    offset = rng.choice([0, 4, 12, 16, 31, 255])
    t.w8(obj + 0x2E, offset)
    destination = data + 256 + rng.randrange(16)
    # Keep the final address in allocated memory while testing 32-bit wrap.
    start = (destination - offset) & 0xFFFFFFFF
    t.w32(obj + 0x18, start if mapped else (old_data + 64 - offset) & 0xFFFFFFFF)
    t.w32(obj + 0x10, start)
    t.w32(obj + 0x94, rng.choice([0, 1, 4, 12, 16, 20, 32]))

    tangent = source + rng.randrange(16)
    # Signed zeros, saturation, ties, subnormals and NaNs/infinities when packing.
    edge_bits = [0, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000,
                 0xFF800000, 0x7FC00000, 0x3F000000, 0xBF000000,
                 0x3F7FFFFF, 0x3F800001, 0x3EAAAAAB, 0x00000001,
                 0x80000001, 0x007FFFFF, 0x00800000]
    if rng.random() < 0.6:
        for k in range(4):
            t.w32((tangent & ~15) + 4 * k, rng.choice(edge_bits))
    t.args(r3=obj, r4=t.u32(), r5=tangent)
