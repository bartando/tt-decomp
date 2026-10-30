"""SWF command-7 float-coordinate triangle lists (formerly pongShadowMap_6920_w).

Valid aligned, non-overlapping command, transform, fill and device storage.
Cover solid/gradient fills, all signed colour channels, clamp boundaries, opacity,
affine world/UV transforms, twip/pixel scaling, stream/count-only modes, wrapping
vertex counters, and nonpositive counts (including signed limits). Guarded output
uses the original vertex emitter, so all 36 bytes of every vertex are compared.
Primitive begin replaces stream state, making prematurely cached state visible.
The gradient boundary supplies per-vertex ARGB samples and records its calls;
gradient interpolation itself, GPU pixels, pointer faults and aliasing are outside
this spec. No ignored memory or float tolerance.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfDrawShapeTriangles"
ADDRESS = 0x82406920
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

DEVICE = 0x825EB988
CURSOR, COUNT_ONLY, COUNT = 0x825EBA74, 0x825EBA84, 0x825EBA88
COLOR, U, V = 0x825CA604, 0x825EBA78, 0x825EBA70


def u32(c, address):
    return int.from_bytes(c.read(address, 4), "big")


def begin(c):
    assert c.r(3) == 3, "triangle-list primitive"
    config = u32(c, DEVICE) + 0x3560
    for i, address in enumerate((CURSOR, COUNT_ONLY, COUNT, COLOR)):
        c.write(address, c.read(config + 4 * i, 4))
    for i, address in enumerate((0x825EBA6C, 0x825EBA80, 0x825EBA8C,
                                 0x82602824, 0x8260283C)):
        c.write(address, c.read(config + 16 + 4 * i, 4))
    c.ret(r3=0)


def gradient(c):
    address = c.r(3)
    index = u32(c, address)
    c.write(address, (index + 1).to_bytes(4, "big"))
    c.ret(r3=u32(c, address + 4 + index * 4))


CALLS = {
    0x82152A78: model(begin, args=("r3", "r4")),
    0x824060B8: model(gradient, args=("r3", "f1", "f2")),
    0x82406010: run(args=("f1", "f2")),
}


def inputs(t):
    r = t.rng
    count = r.choice((0, 0, 1, 2, 3, 6, 9, 17, -1, -2, -0x80000000))
    n = max(count, 0)
    command = t.alloc(4 + n * 8 + 16, "guardedCommand")
    t.w32(command, count)
    t.floats(command + 4, n * 2, -50000, 50000)
    transform = t.alloc(160, "transform")
    t.floats(transform, 12, -10, 10)
    for i in range(8):
        t.w8(transform + 56 + i, r.choice((-128, -127, -65, -64, -1, 0,
                                         1, 63, 64, 65, 127, r.randrange(-128, 128))))
    t.w8(transform + 71, r.choice((0, 1, 127, 254, 255, r.randrange(256))))
    fill = t.alloc(40, "fill")
    t.w32(fill + 4, r.choice((0, 0xFFFFFFFF, 0x01020304, 0x80402010, r.getrandbits(32))))
    t.floats(fill + 8, 6, -10, 10)
    samples = t.alloc(4 + max(n, 1) * 4, "gradientSamples")
    t.w32(samples, 0)
    for i in range(max(n, 1)):
        t.w32(samples + 4 + i * 4, r.getrandbits(32))
    t.w32(fill + 36, samples if r.randrange(2) else 0)

    vertices = t.alloc(16 + max(n, 1) * 36 + 16, "guardedVertices",
                       floats=[(16 + i * 36, 6) for i in range(max(n, 1))] +
                              [(16 + i * 36 + 28, 2) for i in range(max(n, 1))])
    device = t.alloc(0x35A0, "graphicsDevice")
    t.w32(DEVICE, device)
    t.w32(device, 0xDEADBEEF)
    t.w32(device + 13652, r.getrandbits(32) & 0x7FFFFFFF)
    count_only = r.choice((0, 0, 1, 2, 0xFFFFFFFF))
    cursor = 0 if count_only and r.randrange(2) else vertices + 16
    for i, value in enumerate((cursor, count_only,
                                r.choice((0, 1, 0xFFFFFFFF, 0xFFFFFFF8, r.getrandbits(32))),
                                r.getrandbits(32))):
        t.w32(device + 0x3560 + 4 * i, value)
    t.floats(device + 0x3570, 5, -10, 10)
    t.w32(CURSOR, vertices + 16)
    t.w32(COUNT_ONLY, r.getrandbits(32))
    t.w32(COUNT, r.getrandbits(32))
    t.w32(COLOR, r.getrandbits(32))
    for address in (U, V, 0x825EBA6C, 0x825EBA80, 0x825EBA8C,
                    0x82602824, 0x8260283C, 0x8202D110):
        t.wf32(address, r.uniform(-10, 10))
    t.args(r3=t.alloc(20, "unusedShape"), r4=command, r5=transform, r6=fill)
