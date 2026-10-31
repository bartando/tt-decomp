"""0x82155B08: indexed mapped normal read, packed/raw and aligned vector stores.

Mapping can replace stride, normal offset, packed flag and data address.
Exercise exact packed words, 32-bit stride multiplication overflow, absent
attributes and unaligned output pointers. No ignored bytes or FP tolerance.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'util_5B08'
ADDRESS = 0x82155B08
SOURCE = 'src/graphics/grc_vertex_buffer.cpp'
TRIALS = 400
FP_CONTRACT = 'off'


def mapping(c):
    obj = c.r(3)
    c.write(obj + 0x1C, c.read(obj + 0x10, 4))
    c.write(obj + 0xD4, c.read(obj + 0xE0, 4))
    c.write(obj + 0x23, c.read(obj + 0xE4, 1))
    c.write(obj + 0xD8, c.read(obj + 0xDA, 1))
    c.write(obj + 0xDB, b'\x01')
    c.ret(r3=1)


CALLS = {0x82157578: model(mapping, args=('r3',))}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x100, 'buffer')
    fmt = t.alloc(4, 'format')
    data = t.alloc(4096, 'vertices')
    old = t.alloc(4096, 'old vertices')
    out = t.alloc(64, 'output and guards') + 16 + rng.randrange(16)
    present = t.index % 7 != 0
    t.w32(fmt, (t.u32() & ~8) | (8 if present else 0))
    t.w32(obj + 8, fmt)
    mapped = rng.choice((0, 1, 2, 255))
    t.w8(obj + 0xDB, mapped)
    index = rng.randrange(8)
    stride = rng.choice((0, 16, 32, 64, 0x80000010))
    if stride & 0x80000000: index &= ~1
    offset = rng.choice((0, 4, 12, 16, 31, 255))
    packed = rng.choice((0, 1, 255))
    t.w32(obj + 0x1C, data + 16 + rng.randrange(16))
    t.w32(obj + 0x10, data + 16 + rng.randrange(16))
    # The staging cursor is an independent decoy; this is an indexed read.
    t.w32(obj + 0x18, old + 128)
    t.w32(obj + 0xD4, stride if mapped else rng.choice((0, 16, 32)))
    t.w32(obj + 0xE0, stride)
    t.w8(obj + 0x23, offset if mapped else rng.randrange(32))
    t.w8(obj + 0xE4, offset)
    t.w8(obj + 0xD8, packed if mapped else 1-packed % 2)
    t.w8(obj + 0xDA, packed)
    # Fill every potential field with packed edge values and random raw bits.
    for i in range(0, 1024, 4):
        fields = [rng.choice((0x200, 0x201, 0x3FF, 0, 1, 0x1FF, rng.getrandbits(10))) for _ in range(3)]
        word = fields[0] | fields[1] << 10 | fields[2] << 20 | rng.getrandbits(2) << 30
        t.w32(data + i, word)
    t.args(r3=out, r4=obj, r5=index)
