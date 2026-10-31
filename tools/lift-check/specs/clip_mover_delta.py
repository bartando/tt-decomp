"""0x82248DB0: real affine math, DOF virtuals, earlier samples and reset paths.

Only the channel evaluations and input DOF virtuals are modeled. All four
existing matrix/quaternion operations and affine inverse/sqrt callees execute
their originals. Uninitialized matrix padding and stack metadata gaps do not
contribute to these results and are excluded from helper-pointee comparisons;
the complete supplied DOFs are compared, with no ignored output bytes.
"""
import math
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_8DB0_g"
ADDRESS = 0x82248DB0
SOURCE = "src/anim/clip_mover_delta.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def quat(rng):
    values = [rng.uniform(-1, 1) for _ in range(4)]
    length = math.sqrt(sum(v * v for v in values))
    return [v / length for v in values]


def get_value(ctx):
    ctx.ret(r3=ctx.r(3) + 0x10)


def set_value(ctx):
    ctx.write(ctx.r(3) + 0x10, ctx.read(ctx.r(4), 16))


def reset_rotation(ctx):
    ctx.write(ctx.r(3) + 0x10, struct.pack(">4f", 0, 0, 0, 1))


def reset_translation(ctx):
    ctx.write(ctx.r(3) + 0x10, bytes(12))


def evaluate(ctx):
    dof = ctx.r(5)
    kind = ctx.read(dof + 5, 1)[0]
    assert kind in (5, 6)
    assert int.from_bytes(ctx.read(dof, 4), "big") == (0x82027BF4 if kind == 6 else 0x82027B9C)
    assert ctx.read(dof + 4, 1)[0] & 15 == (1 if kind == 6 else 0)
    assert ctx.read(dof + 6, 2) == b"\0\0"
    status = int.from_bytes(ctx.read(ctx.r(3) + (0x20 if kind == 6 else 0x24), 4), "big")
    if status:
        values = quat(ctx.rng) if kind == 6 else [ctx.rng.uniform(-5, 5) for _ in range(4)]
        ctx.write(dof + 0x10, struct.pack(">4f", *values))
    ctx.ret(r3=status)


CALLS = {
    "rotation.vfn_15": model(get_value, args=("r3",)),
    "translation.vfn_14": model(get_value, args=("r3",)),
    "rotation.vfn_18": model(set_value, args=("r3", "r4"), deref={"r4": 16}),
    "translation.vfn_17": model(set_value, args=("r3", "r4"), deref={"r4": 16}),
    "rotation.vfn_13": model(reset_rotation, args=("r3",)),
    "translation.vfn_13": model(reset_translation, args=("r3",)),
    0x82248828: model(evaluate, args=("r3", "r5", "f1")),
    0x8223AD30: run(args=("r3", "r4"), deref={"r4": 16}),
    0x820D7B30: run(args=("r3",)),
    0x820D7B90: run(args=("r3", "r4")),
    0x820C3AD8: run(args=("r3", "r4")),
    0x8223B218: run(args=("r3", "r4")),
    0x824301D0: run(),
}


def inputs(t):
    rng = t.rng
    clip = t.alloc(0x30, "clip")
    t.w32(clip + 0x20, rng.choice([0, 1, 1]))
    t.w32(clip + 0x24, rng.choice([0, 1, 1]))
    rotation = t.alloc(0x20, "rotation", floats=[(0x10, 4)])
    translation = t.alloc(0x20, "translation", floats=[(0x10, 4)])
    t.w32(rotation, t.vtable("rotation", slots=21))
    t.w32(translation, t.vtable("translation", slots=18))
    for i, value in enumerate(quat(rng)):
        t.wf32(rotation + 0x10 + i * 4, value)
    t.floats(translation + 0x10, 4, -5, 5)
    values = [-2.0, -0.0, 0.0, 0.1, 1.0, 5.0, float("nan"), float("inf"), -float("inf"), rng.uniform(-3, 3)]
    values = [struct.unpack(">f", struct.pack(">f", value))[0] for value in values]
    t.args(r3=clip, r4=rng.getrandbits(32), r5=rng.getrandbits(32), r6=rotation,
           r7=translation, f1=rng.choice(values), f2=rng.choice(values))
