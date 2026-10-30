"""Position write: absent attribute and raw copy of positionSize bytes.

Exercise the mapping side effects (data pointer can change), wrapping vertex
offsets and unaligned source/destination. pg_7578_g is modeled at the boundary.
"""
from liftcheck.spec import *

FUNCTION = "grc_69C0"
ADDRESS = 0x821569C0
SOURCE = "src/graphics/grc_vertex_buffer.cpp"


def map_buffer(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x1C, ctx.read(obj + 0x14, 4))
    ctx.write(obj + 0xDB, b"\x01")
    ctx.ret(r3=1)


CALLS = {
    "pg_7578_g": model(map_buffer, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0xE0, "vertexBuffer")
    fmt = t.alloc(4, "format")
    data = t.alloc(1024, "vertices")
    old_data = t.alloc(1024, "oldMapping")
    source = t.alloc(64, "position")

    present = rng.random() < 0.85
    t.w32(fmt, (t.u32() & ~0x1) | (0x1 if present else 0))
    t.w32(obj + 8, fmt)
    mapped = rng.randrange(2)
    t.w8(obj + 0xDB, mapped)

    stride = rng.choice([12, 16, 32, 48, 0x40000000])
    index = rng.choice([0, 1, 3, 0x40000000, 0xFFFFFFFF])
    offset = rng.choice([0, 4, 12, 16, 31, 255])
    address_offset = (stride * index + offset) & 0xFFFFFFFF
    t.w32(obj + 0xD4, stride)
    t.w8(obj + 0x20, offset)
    destination = data + 256 + rng.randrange(16)
    t.w32(obj + 0x1C, ((destination if mapped else old_data + 256) - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x14, (destination - address_offset) & 0xFFFFFFFF)
    t.w32(obj + 0x5C, rng.choice([0, 1, 4, 12, 16, 20, 32]))
    t.args(r3=obj, r4=index, r5=source + rng.randrange(16))
