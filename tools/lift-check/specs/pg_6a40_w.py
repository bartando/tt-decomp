"""Normal write: absent attribute, packed 2:10:10:10 and raw copy.

Exercise the mapping side effects (format and data pointer can change), the
type field at format+4, vector address rounding, unaligned destinations and
raw copies, wrapping vertex offsets and packing boundaries. pg_7578_g is
modeled at the boundary; this checks only pg_6A40_w.
"""
from liftcheck.spec import *

FUNCTION = "pg_6A40_w"
ADDRESS = 0x82156A40
SOURCE = "src/graphics/grc_vertex_buffer.cpp"
FP_CONTRACT = "off"  # VMX multiply/subtract round separately.


def map_buffer(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 8, ctx.read(obj + 0x0C, 4))
    ctx.write(obj + 0x1C, ctx.read(obj + 0x14, 4))
    ctx.write(obj + 0xDB, b"\x01")
    ctx.ret(r3=1)


CALLS = {
    "pg_7578_g": model(map_buffer, args=("r3",)),
}


def write_format(t, address, present, packed):
    rng = t.rng
    flags = (t.u32() & ~0x8) | (0x8 if present else 0)
    other = rng.choice([0, 1, 2, 3, 4, 6, 7])
    kind = (t.u32() & ~0xE00) | ((5 if packed else other) << 9)
    t.w32(address, flags)
    t.w16(address + 4, kind & 0xFFFF)


def inputs(t):
    rng = t.rng
    obj = t.alloc(0xE0, "vertexBuffer")
    fmt = t.alloc(8, "format")
    mapped_fmt = t.alloc(8, "mappedFormat")
    data = t.alloc(1024, "vertices")
    old_data = t.alloc(1024, "oldMapping")
    source = t.alloc(64, "normal")
    t.floats(source, 16, -2, 2)

    mode = rng.randrange(3)  # absent, packed, raw
    mapped = rng.randrange(2)
    write_format(t, fmt, mode != 0, mode == 1)
    # Mapping may flip the packed/raw choice, but not presence (checked first).
    write_format(t, mapped_fmt, True, mode == 1 if rng.random() < 0.7 else mode != 1)
    t.w32(obj + 8, fmt)
    t.w32(obj + 0x0C, mapped_fmt)
    t.w8(obj + 0xDB, mapped)

    stride = rng.choice([12, 16, 32, 48, 0x40000000])
    index = rng.choice([0, 1, 3, 0x40000000, 0xFFFFFFFF])
    offset = rng.choice([0, 4, 12, 16, 31, 255])
    address_offset = (stride * index + offset) & 0xFFFFFFFF
    t.w32(obj + 0xD4, stride)
    t.w8(obj + 0x23, offset)
    # Keep the final address in allocated memory while testing 32-bit wrap.
    destination = data + 256 + rng.randrange(16)
    t.w32(obj + 0x1C, ((destination if mapped else old_data + 256) - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x14, (destination - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x68, rng.choice([0, 1, 4, 12, 16, 20, 32]))

    normal = source + rng.randrange(16)
    # Signed zeros, saturation, ties, subnormals and NaNs/infinities when packing.
    edge_bits = [0, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000,
                 0xFF800000, 0x7FC00000, 0x3F000000, 0xBF000000,
                 0x3F7FFFFF, 0x3F800001, 0x3EAAAAAB, 0x00000001,
                 0x80000001, 0x007FFFFF, 0x00800000]
    if rng.random() < 0.6:
        for k in range(4):
            t.w32((normal & ~15) + 4 * k, rng.choice(edge_bits))
    t.args(r3=obj, r4=index, r5=normal)
