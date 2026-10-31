"""0x821D0880: sampled identity fallback, both composition branches, full matrix."""
import struct
from liftcheck.spec import *

FUNCTION = "phBoundCapsule_0880_g"
ADDRESS = 0x821D0880
SOURCE = "src/anim/bone_transform_lookup.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {"g_identityMatrixRef": 0x825CB800}
IDENTITY = struct.pack(">16f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)


def random_matrix(ctx):
    values = [ctx.rng.uniform(-3, 3) for _ in range(16)]
    if ctx.rng.randrange(3) == 0:
        values[ctx.rng.randrange(16)] = ctx.rng.choice([0.0, -0.0, 1.0e-40, -1.0e-40])
    return struct.pack(">16f", *values)


def sample(ctx):
    assert ctx.read(ctx.r(4), 64) == IDENTITY
    if ctx.rng.choice([False, True]):
        ctx.write(ctx.r(4), random_matrix(ctx))


def euler(ctx):
    # The existing Euler lift writes xyz while preserving the three w lanes.
    data = bytearray(ctx.read(ctx.r(3), 48))
    values = random_matrix(ctx)
    for row in range(3):
        data[row * 16:row * 16 + 12] = values[row * 16:row * 16 + 12]
    ctx.write(ctx.r(3), bytes(data))


def rotate(ctx):
    ctx.write(ctx.r(3), random_matrix(ctx))


CALLS = {
    0x821D0A30: model(sample, args=("r3", "r4", "r5")),
    0x82118278: model(euler, args=("r3", "r4"), deref={"r3": 64, "r4": 12}),
    0x820C3AD8: run(args=("r3", "r4"), deref={"r3": 64, "r4": 64}),
    0x820D05A0: model(rotate, args=("r3", "f1"), deref={"r3": 64}),
    0x82111EA0: model(rotate, args=("r3", "f1"), deref={"r3": 64}),
    0x82175D88: model(rotate, args=("r3", "f1"), deref={"r3": 64}),
}


def inputs(t):
    bone = t.alloc(0x90, "bone", floats=[(0x20, 3), (0x30, 4)])
    t.floats(bone + 0x20, 3, -3, 3)
    t.floats(bone + 0x30, 4, -5, 5)
    storage = t.alloc(96, "matrixAndGuards", floats=[(16, 16)])
    output = storage + 16
    if t.index % 5 == 0:
        output = bone + 0x10
    state = t.alloc(0x20, "samplingState")
    t.w8(bone + 0x42, t.rng.choice([0, 1, 2, 255]))
    t.args(r3=bone, r4=output, r5=state)
