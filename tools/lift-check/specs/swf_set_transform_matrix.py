"""SWF affine transform decomposition (formerly phBoundCapsule_7C60_g).

Exercise rotation removal, signed/zero scales, degenerate columns, shear on both
sides of its thresholds, translation, existing residual translation and input
aliasing the current matrix or later transform fields. Compare call arguments,
full matrices at concat, the entire transform at rebuild, and all memory, without
float tolerance. Include infinities/NaNs, signed zero, subnormals and overflow.

Limits: asin and the rotation builder's sin/cos use Python libm boundary models;
this checks the caller's arithmetic/call contract, not those CRT implementations.
The original rotation builder and concat execute on both sides. Rebuild is a
boundary model so its writes cannot hide the state prepared by this function.
No rendering or native performance claim. Shared mutable shear thresholds are
patched on some trials. The spec assumes valid, 4-byte-aligned transform/matrix
storage; it does not check faults from invalid pointers.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "rage::swfSetTransformMatrix"
ADDRESS = 0x82407C60
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def _asin(ctx):
    value = ctx.f(1)
    ctx.ret(f1=math.asin(value) if abs(value) <= 1.0 else float("nan"))


def _rebuild(ctx):
    assert ctx.read(ctx.r(3) + 0x8D, 1) == b"\x01"
    ctx.write(ctx.r(3) + 0x8D, b"\x00")


CALLS = {
    0x82430E88: model(_asin, args=("f1",)),
    0x823FA2A0: run(),
    0x824302B0: model(lambda ctx: ctx.ret(f1=math.cos(ctx.f(1))), args=("f1",)),
    0x824301D8: model(lambda ctx: ctx.ret(f1=math.sin(ctx.f(1))), args=("f1",)),
    0x823FA1E0: run(),
    0x823FB018: model(_rebuild, args=("r3",), deref={"r3": 0x90}),
}
# run() also records pointees at the call boundary, not just resulting memory.
CALLS[0x823FA1E0].deref = {"r4": 24, "r5": 24}


def inputs(t):
    rng = t.rng
    transform = t.alloc(0x90, "transform")
    t.floats(transform + 0x48, 17, -100, 100)
    matrix = rng.choice((t.alloc(24, "matrix"), transform, transform + 4,
                         transform + 0x3C, transform + 0x40, transform + 0x48,
                         transform + 0x70))
    mode = rng.randrange(7)
    if mode == 0:
        # Axis aligned, including a degenerate second column and signed zero.
        values = [rng.choice((0.0, -0.0, -2.0, 1.0, 3.0)), 0.0,
                  rng.choice((0.0, -0.0)), rng.choice((0.0, -0.0, -2.0, 1.0)), 0.0, 0.0]
    elif mode == 1:
        # No rotation: exact inclusive shear boundaries and their adjacent floats.
        bits = rng.choice((0, 0x80000000, 0x3C23D709, 0x3C23D70A, 0x3C23D70B,
                           0xBC23D709, 0xBC23D70A, 0xBC23D70B))
        values = [rng.uniform(-5, 5), struct.unpack(">f", struct.pack(">I", bits))[0],
                  0.0, rng.choice((-1.0, 0.0, 1.0)), 0.0, 0.0]
    elif mode == 2:
        angle = rng.uniform(-math.pi, math.pi)
        sx, sy = rng.uniform(-4, 4), rng.uniform(-4, 4)
        values = [sx * math.cos(angle), sx * math.sin(angle),
                  -sy * math.sin(angle), sy * math.cos(angle), 0.0, 0.0]
    elif mode == 3:
        # Near the rotation-removal stopping threshold (degrees +/-1e-6).
        values = [1.0, rng.uniform(-0.1, 0.1),
                  rng.choice((-1, 1)) * rng.uniform(1.6e-8, 1.9e-8), 1.0, 0.0, 0.0]
    elif mode == 4:
        values = [rng.uniform(-5, 5) for _ in range(6)]
    elif mode == 5:
        values = [rng.choice((float("nan"), float("inf"), -float("inf"), -0.0)),
                  rng.choice((float("nan"), float("inf"), -float("inf"), -0.0)),
                  rng.choice((float("nan"), float("inf"), -float("inf"), 0.0)),
                  rng.choice((float("nan"), float("inf"), -float("inf"), 1.0)), 0.0, 0.0]
    else:
        # Overflow/underflow in squared length, and tiny finite columns.
        values = [rng.uniform(-5, 5), 0.0,
                  rng.choice((1e-40, -1e-30, 1e20, -3.4028234663852886e38)),
                  rng.choice((0.0, -1e-40, 1e-30, 1e20)), 0.0, 0.0]
    values[4:] = [rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)]
    if mode == 5:
        values[4:] = [rng.choice((float("nan"), float("inf"), -float("inf"), -0.0))
                      for _ in range(2)]
    for i, value in enumerate(values):
        t.wf32(matrix + 4 * i, value)
    if mode != 1 and rng.randrange(3) == 0:
        t.wf32(0x825C90C8, rng.choice((-0.0, -0.005, -0.1)))
        t.wf32(0x825C8078, rng.choice((0.0, 0.005, 0.1)))
    t.args(r3=transform, r4=matrix)
