"""Shared valid stream state for the three SWF stroke specs.

Original vertex emission executes on both sides: position, normal, colour, UV,
cursor, wrapping count and guard bytes are compared. No ignored memory or float
tolerance. Matrices, input twips and pixel scales vary independently; one value
can be exceptional (subject to lift-check's NaN/signed-zero comparison rules).
Only valid aligned, nonaliasing state is supported; this checks CPU geometry
and call boundaries, not GPU pixels or a live match.
"""
import struct

STATE = 0x8260613C
DEVICE = 0x825EB988
CURSOR, COUNT_ONLY, COUNT = 0x825EBA74, 0x825EBA84, 0x825EBA88
COLOR = 0x825CA604
FLOATS = (0x825EBA6C, 0x825EBA80, 0x825EBA8C, 0x825EBA78,
          0x825EBA70, 0x82602824, 0x8260283C)
SPECIAL = (0, 0x80000000, 1, 0x80000001, 0x00800000, 0x7F7FFFFF,
           0xFF7FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def value(r):
    return f32(r.choice((0.0, -0.0, 1.0, -1.0, r.uniform(-10000, 10000))))


def stream(t):
    r = t.rng
    vertices = t.alloc(16 + 6 * 36 + 16, "guardedLineVertices",
                       floats=[(16 + 36 * i, 6) for i in range(6)] +
                              [(16 + 36 * i + 28, 2) for i in range(6)])
    device = t.alloc(0x3600, "graphicsDevice")
    t.w32(DEVICE, device)
    t.w32(device, 0xDEADBEEF)
    t.w32(device + 13652, r.getrandbits(31))
    count_only = r.choice((0, 0, 1, 2, 0x80000000, 0xFFFFFFFF))
    cursor = 0 if count_only and r.randrange(2) else vertices + 16
    words = (cursor, count_only,
             r.choice((0, 1, 0xFFFFFFFA, 0xFFFFFFFF, r.getrandbits(32))),
             r.getrandbits(32))
    for i, address in enumerate((CURSOR, COUNT_ONLY, COUNT, COLOR)):
        t.w32(address, words[i])
        t.w32(device + 0x3560 + 4 * i, words[i])
    t.floats(STATE, 12, -10, 10)
    t.floats(device + 0x3570, 12, -10, 10)
    for i, address in enumerate(FLOATS):
        t.wf32(address, r.uniform(-10, 10))
        t.wf32(device + 0x35A0 + 4 * i, r.uniform(-10, 10))
    if r.randrange(4) == 0:
        # Separate UV/display transforms catch using offset coordinates for UVs.
        base = r.choice((STATE, device + 0x3570))
        t.w32(base + 4 * r.randrange(12), r.choice(SPECIAL))
    t.wf32(0x8202D110, r.uniform(-10, 10))


def begin(c):
    assert (c.r(3), c.r(4)) == (5, 6), "stroke must begin a six-vertex triangle fan"
    device = int.from_bytes(c.read(DEVICE, 4), "big")
    # Begin can replace the stream and render transforms. Geometry must use the
    # resulting state; cleanup must inspect the cursor after the six emissions.
    for i, address in enumerate((CURSOR, COUNT_ONLY, COUNT, COLOR)):
        c.write(address, c.read(device + 0x3560 + 4 * i, 4))
    c.write(STATE, c.read(device + 0x3570, 48))
    for i, address in enumerate(FLOATS):
        c.write(address, c.read(device + 0x35A0 + 4 * i, 4))
    c.ret(r3=0)


def vertex_inputs(t):
    stream(t)
    r = t.rng
    args = [value(r) for _ in range(3)]
    if r.randrange(4) == 0:
        args[r.randrange(3)] = struct.unpack(">f", struct.pack(">I", r.choice(SPECIAL)))[0]
    t.args(f1=args[0], f2=args[1], f3=args[2])
