"""All shape opcodes, repeated one-based styles and zero-index retention,
unknown words, metadata skip, default styles, independent/connected strokes,
integer fans and float triangles, texture override and gradient/solid fills.

Valid terminated, nonaliasing streams; polyline count >=1, segment count >=0,
fan count >0 (the original loops forever on zero). <=4 points per primitive
keeps 1000 trials quick. Stroke setup/drawing and gradient/triangle rendering
are boundaries whose arguments and consumed state are recorded in guarded
memory. Fan vertices execute the original emitter, checking every written byte.
No ignored memory or tolerance. GPU output/gradient interpolation are not tested.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::swfSHAPE::Render"
ADDRESS = 0x82406C58
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

DEVICE, UV, MATRIX = 0x825EB988, 0x8260613C, 0x82606154
CURSOR, COUNT_ONLY, COUNT = 0x825EBA74, 0x825EBA84, 0x825EBA88
COLOR, U, V = 0x825CA604, 0x825EBA78, 0x825EBA70


def u32(c, p):
    return int.from_bytes(c.read(p, 4), 'big')


def record(c, data):
    # Caller-owned log records style/global state at each rendering boundary.
    device = u32(c, DEVICE)
    log = u32(c, device + 0x3560)
    offset = u32(c, log)
    c.write(log + 4 + offset, data)
    c.write(log, (offset + len(data)).to_bytes(4, 'big'))


def stroke(c):
    p = c.r(3)
    record(c, c.read(p, 2) + c.read(p + 4, 4) + c.read(MATRIX, 24))
    c.write(COLOR, c.read(p + 4, 4))


def line(c):
    record(c, c.read(COLOR, 4) + c.read(UV, 48))


def bind(c):
    record(c, c.r(3).to_bytes(4, 'big') + c.read(UV, 48))


def begin(c):
    device = u32(c, DEVICE)
    c.write(CURSOR, c.read(device + 0x3564, 4))
    c.write(COUNT_ONLY, c.read(device + 0x3568, 4))


def gradient(c):
    record(c, c.read(COLOR, 4))
    c.ret(r3=c.rng.getrandbits(32))


def triangles(c):
    fill = c.r(6)
    # Skip the unused/padding first four bytes of the fill (default type is
    # only a byte store in the original); record every semantically read field.
    record(c, c.read(fill + 4, 36) + c.read(UV, 48))
    c.ret(r3=u32(c, c.r(4)) * 2 + 1)


CALLS = {
    0x82406290: model(stroke, args=("r3", "r4")),
    0x82406778: model(line, args=("f1", "f2", "f3", "f4", "f5")),
    "bind": model(bind, args=("r3",)),
    0x82152A78: model(begin, args=("r3", "r4")),
    0x824060B8: model(gradient, args=("r3", "f1", "f2")),
    0x82406920: model(triangles, args=("r3", "r4", "r5", "r6"), deref={"r6": 0}),
    0x82406010: run(args=("f1", "f2")),
}


def inputs(t):
    r = t.rng
    shape = t.alloc(32, 'shape')
    fills = t.alloc(3 * 40, 'fills')
    strokes = t.alloc(3 * 8, 'strokes')
    transform = t.alloc(160, 'transform')
    t.floats(transform, 12, -10, 10)
    for i in range(8):
        t.w8(transform + 56 + i, r.choice((0, 1, 63, 64, 65, 127, 128, 192, 255, r.randrange(256))))
    t.w8(transform + 71, r.choice((0, 1, 127, 254, 255)))
    t.w8(transform + 140, r.choice((0, 0, 1, 2, 255)))
    for i in range(3):
        f = fills + 40 * i
        texture = t.alloc(12, 'texture') if r.randrange(2) else 0
        t.w32(f + 4, r.choice((0, 0xFFFFFFFF, 0x01020304, r.getrandbits(32))))
        t.floats(f + 8, 6, -10, 10)
        t.w32(f + 32, texture)
        t.w32(f + 36, t.alloc(4, 'gradient') if r.randrange(2) else 0)
        t.w16(strokes + 8 * i, r.choice((0, 1, 20, 255, 0x8000, 0xFFFF)))
    words = []
    def emit(op):
        if op in (1, 2, 6, 7):
            n = r.randrange(1 if op in (1, 2) else 0, 5)
            words.extend((op, n))
            points = n * 2 if op == 6 else n
            for _ in range(points):
                if op == 2:
                    words.extend((r.choice((0, 1, -1, 0x7FFFFFFF, -0x80000000, r.randrange(-100000, 100000))),
                                  r.randrange(-100000, 100000)))
                else:
                    words.extend(struct.unpack('>II', struct.pack('>ff', r.uniform(-1e4, 1e4), r.uniform(-1e4, 1e4))))
            if op == 7 and n:
                words[-1] = 0 # A one-word under-advance must terminate before later draws.
        elif op == 3:
            words.extend((3, 0, 7))  # Must skip both, even though they look like opcodes.
        elif op in (4, 5):
            words.extend((op, r.randrange(4)))
        else:
            words.append(op)
    # Deterministic early cases expose each path; random scripts mix state.
    sequence = ((t.index % 8,) if t.index < 8 else
                r.choice(((1, 6), (2,), (7,), (4, 2, 4, 7), (5, 1, 5, 6),
                          (8, 0xFFFFFFFF, 3, 4, 5, 2, 7, 1, 6))))
    for op in sequence:
        emit(op)
    words.append(0)
    command = t.alloc(len(words) * 4, 'commands')
    for i, word in enumerate(words):
        t.w32(command + 4 * i, word & 0xFFFFFFFF)
    for offset, pointer in ((8, fills), (12, strokes), (16, command)):
        t.w32(shape + offset, pointer)
    device = t.alloc(0x3580, 'device')
    log = t.alloc(8192, 'renderBoundaryLog')
    t.w32(log, 0)
    vertices = t.alloc(16 + 16 * 36 + 16, 'guardedVertices') + 16
    t.w32(DEVICE, device)
    t.w32(device + 0x3560, log)
    count_only = r.choice((0, 0, 1, 2))
    t.w32(device + 0x3564, 0 if count_only and r.randrange(2) else vertices)
    t.w32(device + 0x3568, count_only)
    t.w32(CURSOR, r.choice((0, vertices)))
    t.w32(COUNT_ONLY, r.getrandbits(32))
    t.w32(COUNT, r.getrandbits(32))
    for p in (0x825EBA6C, 0x825EBA80, 0x825EBA8C, U, V, 0x82602824, 0x8260283C):
        t.wf32(p, r.uniform(-10, 10))
    t.w32(0x82602820, t.fake_fn('bind'))
    t.args(r3=shape, r4=transform, r5=r.getrandbits(32))
