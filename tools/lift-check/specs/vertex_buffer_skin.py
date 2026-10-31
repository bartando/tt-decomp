"""0x82155510: four palette influences, staging reads/writes and cursor advance.

Use original attribute helpers on both sides; mapping is a scripted boundary.
Inputs cover null/self/separate output, nonpositive counts, all attribute gates,
alignment, packed normals/tangents, non-normalized weights and matrix rounding.
Absent source scratch is only exercised when its corresponding output is absent.
"""
import struct
from liftcheck.spec import *
from liftcheck.machine import ARENA_BASE

FUNCTION = 'pg_5510_g'
ADDRESS = 0x82155510
SOURCE = 'src/graphics/grc_vertex_buffer.cpp'
TRIALS = 120
FP_CONTRACT = 'off'
FTOL = 0


def mapping(c):
    obj = c.r(3)
    c.write(obj + 0x1C, c.read(obj + 0x10, 4))
    c.write(obj + 0xDB, b'\x01')
    c.ret(r3=1)


CALLS = {
    0x825696A4: run(transparent=True, args=()),
    0x8256993C: run(transparent=True, args=()),
    0x82157578: model(mapping, args=('r3',)),
    0x821554B0: run(args=('r3', 'r4')),
    0x82155BD8: run(args=('r4',)),
    0x82156B20: run(args=('r3', 'r4')),
}


def inputs(t):
    rng = t.rng
    count = (-3, 0, 1, 2, 4, 3)[t.index % 6]
    n = max(count, 1)
    source = t.alloc(0x100, 'source buffer')
    separate = t.index % 3 == 2
    output = t.alloc(0x100, 'output buffer') if separate else source
    pose = t.alloc(32 * 64, 'bone matrices')
    palette = t.alloc(512, 'byte-indexed bone palette')
    for i in range(256):
        t.w16(palette + 2*i, rng.randrange(32))
    t.floats(pose, 32 * 16, -4, 4)
    # Cancellation, subnormals and signed zero catch VMX rounding/flush errors.
    if t.index % 7 == 0:
        for i in range(32 * 16):
            t.w32(pose + i*4, rng.choice((0x3F800001, 0xBF800000, 0x00800000,
                                        0x00000001, 0x80000001, 0, 0x80000000,
                                        0x41800001, 0xC1800000)))
    if t.index % 17 == 14:
        t.put(pose, bytes(32*64))
        for i in range(32):
            t.w32(pose + i*64 + 48, 0x007FFFFF)
    flags = rng.choice((0x400F, 0x400F, 0x400D, 0x400B, 0x4009))
    # Undefined input scratch is never exposed as an enabled output attribute.
    if separate:
        outflags = rng.choice((0, 1, 8, 0x4000, 0x4009))
        flags = (flags & ~0x4009) | outflags
    else:
        outflags = flags
    if t.index % 17 == 14:
        flags |= 0x400F
        outflags |= 0x4009
    for obj, f, is_source in ((source, flags, True), (output, outflags, False)):
        if obj == source and not is_source:
            continue
        fmt = t.alloc(16, 'vertex format')
        t.w32(fmt, f)
        t.w32(obj + 8, fmt)
        stride = rng.choice((112, 128, 160))
        data = t.alloc((n + 2) * stride + 64, 'source vertices' if is_source else 'output vertices')
        data += 16 + rng.randrange(4) * 4
        t.w32(obj + 0x10, data)
        t.w32(obj + 0x1C, data)
        t.w32(obj + 0x18, data + 7)  # begin must replace this old cursor
        t.w32(obj + 0xD4, stride)
        t.w8(obj + 0xDB, rng.choice((0, 1, 2, 255)))
        t.w8(obj + 0x3E, 1 if f & 1 else rng.randrange(2))
        posoff = rng.randrange(4)*4
        t.w8(obj + 0x20, posoff)
        t.w8(obj + 0x21, 32 + rng.randrange(16))
        t.w8(obj + 0x22, 80 + rng.randrange(4)*4)
        t.w8(obj + 0x23, 48 + rng.randrange(16))
        t.w8(obj + 0x2E, 64 + rng.randrange(16))
        t.w32(obj + 0x5C, rng.choice((0, 4, 8, 12, 16)))
        t.w32(obj + 0x94, rng.choice((0, 4, 8, 12, 16)))
        t.w8(obj + 0xD8, rng.randrange(2))
        t.w8(obj + 0xD9, rng.randrange(2))
        # First write ordinary floats, then exact integer indices / packed data.
        t.floats(data & ~15, ((n + 1)*stride)//4, -3, 3)
        if is_source:
            def b(off): return t.arena[obj + off - ARENA_BASE]
            for v in range(n):
                base = data + v*stride
                t.w32(base + b(0x22), rng.getrandbits(32))
                if b(0xD8):
                    t.w32(base + b(0x23), rng.getrandbits(32))
                waddr = (base + b(0x21)) & ~15
                if t.index % 17 == 14:
                    for lane in range(4):
                        t.wf32(waddr + lane*4, 2.0 if lane == 0 else 0.0)
                elif t.index % 7 == 0:
                    for lane in range(4):
                        t.w32(waddr + lane*4, rng.choice((0x3F800001, 0xBF800000, 0x3F000000,
                                                        0x00000001, 0x80000001)))
    t.args(r3=source, r4=pose + (t.index % 4)*4, r5=rng.getrandbits(32), r6=palette,
           r7=rng.getrandbits(32), r8=count, r9=output if t.index % 3 else 0)
