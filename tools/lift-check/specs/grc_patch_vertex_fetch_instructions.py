"""Patch actual Xenon fetch words: format swizzles, absent attributes, stream
strides, signed normalization, group sorting, fixed last fetches and bursts.

Valid <=32-fetch shader metadata and <=16 vertex elements; instruction output
can alias shader templates. Inputs include duplicate/missing attributes, all
format-size table entries, zero fetches, unsorted/tied/negative offsets, burst
spans 0/1/8/9, and duplicate destination indices. All output/guard bytes compare
exactly; no stubs, ignores or tolerance. GPU execution is outside this spec.
"""
from liftcheck.spec import *

FUNCTION = "grcPatchVertexFetchInstructions"
ADDRESS = 0x82362A68
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 1000


def inputs(t):
    r = t.rng
    count = (0, 1, 2, 3, 5, 8, 12, 16, 24, 32)[t.index % 10]
    shader = t.alloc(0x280, "shader")
    declaration = t.alloc(0x24 + 16 * 12, "declaration")
    device = t.alloc(0x31B0, "device")
    code = t.alloc(16 + 32 * 12 + 16, "guardedCode") + 16
    if t.index % 13 == 0:
        code = shader + 0xB8
    elements = r.choice((0, 1, 2, 4, 8, 16))
    t.w32(shader + 0x34, count)
    t.w32(declaration + 8, elements)
    semantic = [(r.randrange(16), r.randrange(16)) for _ in range(16)]
    for i in range(elements):
        e = declaration + 0x24 + i * 12
        t.w16(e, r.randrange(16))
        t.w16(e + 2, r.choice((0, 4, 8, 28, 32, 0xFFFC, r.randrange(65536))))
        t.w32(e + 4, r.getrandbits(32))
        t.w8(e + 9, semantic[i][0])
        t.w8(e + 10, semantic[i][1])
    for i in range(16):
        t.w8(device + 0x3190 + i, r.choice((0, 1, 4, 16, 64, 255)))
    mode = t.index % 7
    for i in range(count):
        usage, index = r.choice(semantic[:max(elements, 1)]) if r.randrange(4) else (15, 15)
        boundary = (r.randrange(4) if mode == 0 else
                    (1 if i == 0 else 3 if i == count - 1 else 0) if mode == 1 else
                    (1 if i % 4 == 0 else 2 if i % 4 == 3 else 0) if mode == 2 else
                    (r.choice((1, 2, 3)) if mode == 3 else 0))
        destination = r.randrange(max(count, 1)) if mode == 4 else i
        t.w32(shader + 0x38 + 4 * i, destination | usage << 12 | index << 16 | boundary << 20)
        p = shader + 0xB8 + i * 12
        opcode = r.getrandbits(32)
        offset = r.getrandbits(32)
        if mode in (1, 2, 3, 5):
            # Repeated constants and nearby offsets force ties and burst merges.
            opcode = (opcode & ~0x07FC0000) | r.choice((0, 1, 2, 3)) << 25
            offset = (offset & 0x800000FF) | r.choice((0, 1, 4, 7, 8, 9, 0x7FFFFF)) << 8
        t.w32(p, opcode)
        t.w32(p + 4, r.getrandbits(32))
        t.w32(p + 8, offset)
    t.args(r3=device, r4=shader, r5=code, r6=declaration)
