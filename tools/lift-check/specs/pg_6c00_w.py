"""Tangent write: absent attribute, handedness, packed 2:10:10:10 and raw copy.

Exercise mapping side effects, optional bitangent fetch, vector address rounding,
unaligned raw copies, wrapping vertex offsets, aliases, and packing boundaries.
The two callees are modeled at the boundary; this checks only pg_6C00_w.
"""
import struct

from liftcheck.spec import *

FUNCTION = "pg_6C00_w"
ADDRESS = 0x82156C00
SOURCE = "src/graphics/grc_vertex_buffer.cpp"
FP_CONTRACT = "off"  # VMX multiply/subtract round separately.


def map_buffer(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 8, ctx.read(obj + 0x0C, 4))
    ctx.write(obj + 0x1C, ctx.read(obj + 0x14, 4))
    ctx.write(obj + 0xDB, b"\x01")
    ctx.ret(r3=1)


def fetch_bitangent(ctx):
    out, obj = ctx.r(3), ctx.r(4)
    values = [ctx.rng.uniform(-2, 2) for _ in range(4)]
    ctx.write(out, struct.pack(">4f", *values))
    # Some callers alias T with the buffer: check the pre-call snapshot and
    # post-call reload separately, and don't assume the helper returns out.
    source = int.from_bytes(ctx.read(obj + 0x18, 4), "big")
    if source:
        ctx.write(source, struct.pack(">4f", *reversed(values)))
        out = source
    ctx.ret(r3=out)


CALLS = {
    "pg_7578_g": model(map_buffer, args=("r3",)),
    "util_5B08": model(fetch_bitangent, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0xE0, "vertexBuffer")
    fmt = t.alloc(4, "format")
    mapped_fmt = t.alloc(4, "mappedFormat")
    data = t.alloc(1024, "vertices")
    old_data = t.alloc(1024, "oldMapping")
    vectors = [t.alloc(64, name) for name in ("tangent", "normal", "bitangent")]
    for vector in vectors:
        t.floats(vector, 16, -2, 2)

    mode = rng.randrange(5)  # absent, handedness with/without B, packed, raw
    mapped = rng.randrange(2)
    flags = (t.u32() & ~0x404000) | (0x4000 if mode else 0)
    if mode >= 3:
        flags |= 0x400000
    t.w32(fmt, flags)
    # Mapping may change the format branch, as well as the data pointer.
    t.w32(mapped_fmt, flags ^ rng.choice([0, 0x400000]))
    t.w32(obj + 8, fmt)
    t.w32(obj + 0x0C, mapped_fmt)
    t.w8(obj + 0xDB, mapped)
    t.w8(obj + 0xD9, 1 if mode == 3 else rng.choice([0, 0, 1, 255]))
    stride = rng.choice([16, 32, 48, 64, 0x40000000])
    index = rng.choice([0, 1, 3, 0x40000000, 0xFFFFFFFF])
    offset = rng.choice([0, 4, 16, 31, 48, 255])
    address_offset = (stride * index + offset) & 0xFFFFFFFF
    t.w32(obj + 0xD4, stride)
    t.w8(obj + 0x2E, offset)
    # Keep the final address in allocated memory while testing 32-bit wrap.
    destination = data + 256 + rng.randrange(16)
    t.w32(obj + 0x1C, ((destination if mapped else old_data + 256) - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x14, (destination - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x94, rng.choice([0, 1, 4, 12, 16, 20, 32]))

    tangent, normal, bitangent = [v + rng.randrange(16) for v in vectors]
    if rng.random() < 0.15:
        normal = tangent  # exact-zero cross/dot and input aliasing
    if rng.random() < 0.15:
        bitangent = tangent
    t.w32(obj + 0x18, (tangent & ~15) if rng.random() < 0.2 else 0)
    # Signed zeros, saturation, ties and NaNs/infinities in the packing path.
    edge_bits = [0, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000,
                 0xFF800000, 0x7FC00000, 0x3F000000, 0xBF000000,
                 0x3F7FFFFF, 0x3F800001, 0x3EAAAAAB, 0x00000001,
                 0x80000001, 0x007FFFFF, 0x00800000]
    if rng.random() < 0.6:
        for k in range(4):
            t.w32((tangent & ~15) + 4 * k, rng.choice(edge_bits))
    if mode == 2:
        # Pin the VMX flush regression: without FTZ, N dot (T cross B) is
        # negative and chooses +1; the original flushes it to zero and writes -1.
        flags = (flags | 0x4000) & ~0x400000
        t.w32(fmt, flags)
        t.w32(mapped_fmt, flags)
        tangent, normal, bitangent = vectors
        for vector, words in zip(vectors, ([1, 0, 0, 0], [0, 0, 0x3F800000, 0],
                                         [0, 0xBF800000, 0, 0])):
            for k, bits in enumerate(words):
                t.w32(vector + 4 * k, bits)
    t.args(r3=obj, r4=index, r5=t.u32(), r6=tangent, r7=normal,
           r8=0 if mode == 1 else bitangent)
