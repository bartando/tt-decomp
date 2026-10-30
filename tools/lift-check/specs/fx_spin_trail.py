"""0x82389740: 31 spin-trail quads, with the original rotation/colour/emitter.

Compare call arguments, colour snapshots, all 124 vertices and batch teardown.
The begin boundary sets stream state (including count-only/null-cursor), as the
real renderer does; GPU setup/pixels are outside this test. Inputs are disjoint
and aligned. Cover general and coordinate axes, zero axis, signed/zero radius,
nonuniform transform rows, finite subnormal lanes/radii, independent RGBA
channels and all 50 height slots. Scalar radius inputs obey the float32 ABI.
No ignored bytes or float tolerance. The adapter only moves the billboard's
packed colour from PPC32 r4 to Xenon r10; it contains no effect logic.
"""
import struct

from liftcheck.spec import *

FUNCTION = "fxBallSpinTex::DrawSpinTrail"
ADDRESS = 0x82389740
SOURCE = "tools/lift-check/specs/fx_spin_trail_adapter.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None
EXTERNS = {"spinTrailBillboardXenon": 0x82410058}

DEVICE = 0x825EB988
CURSOR, COUNT_ONLY, COUNT = 0x825EBA74, 0x825EBA84, 0x825EBA88


def u32(c, addr):
    return int.from_bytes(c.read(addr, 4), "big")


def begin(c):
    assert (c.r(3), c.r(4)) == (6, 124), "one 124-vertex quad batch"
    device = u32(c, DEVICE)
    for k, addr in enumerate((CURSOR, COUNT_ONLY, COUNT)):
        c.write(addr, c.read(device + 0x3560 + k * 4, 4))
    c.ret(r3=0)


CALLS = {
    0x82152A78: model(begin, args=("r3", "r4")),
    0x820C3DA0: run(args=("r3", "r4", "f1"), deref={"r4": 16}),
    0x820C3F10: run(args=("r3", "f1")),
    0x820C3F98: run(args=("r3", "f1")),
    0x820C4020: run(args=("r3", "f1")),
    0x820C40A8: run(args=("r3", "r4", "f1"), deref={"r4": 16}),
    0x824302B0: run(args=("f1",)),
    0x824301D8: run(args=("f1",)),
    0x8223F840: run(args=("r3", "r4"), deref={"r4": 16}),
    0x82410058: run(args=("r3", "r10", "f1", "f2", "f3", "f4", "f5", "f6")),
}


def inputs(t):
    r = t.rng
    effect = t.alloc(64 * 50 + 128, "effectAndHeightSamples")
    for k in range(50):
        t.wf32(effect + k * 64 + 104, r.uniform(-20, 20))
    t.w32(0x825C4898, r.randrange(50))
    matrix = t.alloc(64, "transform")
    t.floats(matrix, 16, -5, 5)
    tiny = 2.0 ** -149
    if r.randrange(5) == 0:
        for k in (4, 5, 6, 12, 13, 14):
            t.wf32(matrix + k * 4, r.choice((0.0, -0.0, tiny, -tiny)))
    axis = t.alloc(16, "spinAxis")
    t.floats(axis, 4, -10, 10)
    kind = r.randrange(9)
    if kind < 7:
        for k in range(3):
            t.wf32(axis + k * 4, 0.0)
        if kind < 6:
            t.wf32(axis + (kind // 2) * 4, r.uniform(0.1, 5) * (-1 if kind & 1 else 1))
    color = t.alloc(16, "color")
    for k in range(4):
        t.wf32(color + k * 4, r.choice((0.0, 1.0, -0.25, 1.25, r.random())))
    radius = r.choice((0.0, -0.0, 1.0, -1.0, tiny, -tiny, r.uniform(-10, 10)))

    vertices = t.alloc(16 + 124 * 36 + 16, "guardedVertices")
    device = t.alloc(0x3580, "graphicsDevice")
    t.w32(DEVICE, device)
    t.w32(device + 13652, r.getrandbits(32))
    count_only = r.choice((0, 0, 1, 2, 0xFFFFFFFF))
    cursor = 0 if count_only and r.randrange(2) else vertices + 16
    for k, value in enumerate((cursor, count_only, r.getrandbits(32))):
        t.w32(device + 0x3560 + k * 4, value)
    # Stale pre-begin state must never be cached by the lift.
    t.w32(CURSOR, 0)
    t.w32(COUNT_ONLY, r.getrandbits(32))
    t.w32(COUNT, r.getrandbits(32))
    uv = t.alloc(16, "billboardUV")
    t.floats(uv, 4, -2, 2)
    t.w32(0x825C2B10, uv)
    t.floats(0x82715FB0, 8, -2, 2)
    t.args(r3=effect, r4=matrix, r5=axis, r6=color, f1=struct.unpack(">f", struct.pack(">f", radius))[0])
