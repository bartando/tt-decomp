"""Staging-vertex normal read: absent attribute, unpacked 2:10:10:10 and raw copy.

The mapping helper can replace the staging pointer and the packed flag, which
the original reads only after the call. Packed words cover every field edge
(-512 -> NaN, -511, 0, 511) and random values; the raw path reads the aligned
16 bytes around the staging address. pg_7578_g is modeled at the boundary.
"""
from liftcheck.spec import *

FUNCTION = "pg_5BD8_g"
ADDRESS = 0x82155BD8
SOURCE = "src/graphics/grc_vertex_buffer.cpp"
FP_CONTRACT = "off"  # VMX multiply/subtract round separately.


def map_buffer(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x18, ctx.read(obj + 0x10, 4))
    ctx.write(obj + 0xD8, ctx.read(obj + 0xDA, 1))
    ctx.write(obj + 0xDB, b"\x01")
    ctx.ret(r3=1)


CALLS = {
    "pg_7578_g": model(map_buffer, args=("r3",)),
}


def packed_word(rng):
    if rng.random() < 0.5:
        return rng.getrandbits(32)
    fields = [rng.choice([0x200, 0x201, 0x3FF, 0, 1, 0x1FF, rng.getrandbits(10)]) for _ in range(3)]
    return fields[0] | fields[1] << 10 | fields[2] << 20 | rng.getrandbits(2) << 30


def inputs(t):
    rng = t.rng
    obj = t.alloc(0xE0, "vertexBuffer")
    fmt = t.alloc(4, "format")
    data = t.alloc(512, "staging")
    old_data = t.alloc(512, "oldStaging")
    out = t.alloc(48, "out")

    present = rng.random() < 0.85
    t.w32(fmt, (t.u32() & ~0x8) | (0x8 if present else 0))
    t.w32(obj + 8, fmt)
    mapped = rng.randrange(2)
    t.w8(obj + 0xDB, mapped)
    packed = rng.choice([0, 1, 1, 255])
    t.w8(obj + 0xD8, packed)
    t.w8(obj + 0xDA, packed if rng.random() < 0.7 else rng.choice([0, 1]))

    offset = rng.choice([0, 4, 12, 16, 31, 255])
    t.w8(obj + 0x23, offset)
    source = data + 256 + rng.randrange(16)
    start = (source - offset) & 0xFFFFFFFF
    old = old_data + 256 + rng.randrange(16)
    t.w32(obj + 0x18, start if mapped else (old - offset) & 0xFFFFFFFF)
    t.w32(obj + 0x10, start)
    for word in (source, old):
        t.w32(word, packed_word(rng))
    t.args(r3=out + rng.randrange(16), r4=obj)
