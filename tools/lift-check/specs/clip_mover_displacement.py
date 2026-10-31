"""0x82248C58: mover metadata, call sequence, clamps and the complete 32-byte result.

Models check the original DOF vtable/type/id/low flag nibble, and pass real
sample bytes between the evaluations and delta call. Uninitialized reserved
bytes and the original flags' high nibble are never consumed or compared.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_ExtractDisplacement"
ADDRESS = 0x82248C58
SOURCE = "src/anim/clip_mover_displacement.cpp"
TRIALS = 1000


def r32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def check_dof(ctx, address, kind):
    assert r32(ctx, address) == (0x82027BF4 if kind == 6 else 0x82027B9C)
    assert ctx.read(address + 4, 1)[0] & 0x0F == (1 if kind == 6 else 0)
    assert ctx.read(address + 5, 1)[0] == kind
    assert ctx.read(address + 6, 2) == b"\0\0"


def evaluate(ctx):
    destination = ctx.r(5)
    kind = ctx.read(destination + 5, 1)[0]
    assert kind in (5, 6)
    check_dof(ctx, destination, kind)
    status = r32(ctx, ctx.r(3) + (0x20 if kind == 6 else 0x24))
    if status & 0xFF:
        ctx.write(destination + 0x10, ctx.rng.randbytes(16))
    ctx.ret(r3=status)


def extract_delta(ctx):
    rotation, translation = ctx.r(6), ctx.r(7)
    check_dof(ctx, rotation, 6)
    check_dof(ctx, translation, 5)
    status = r32(ctx, ctx.r(3) + 0x28)
    if status & 0xFF:
        ctx.write(rotation + 0x10, bytes(v ^ 0x33 for v in ctx.read(rotation + 0x10, 16)))
        ctx.write(translation + 0x10, bytes(v ^ 0xA5 for v in ctx.read(translation + 0x10, 16)))
    ctx.ret(r3=status)


CALLS = {
    0x82248828: model(evaluate, args=("r3", "r5", "f1")),
    0x82248DB0: model(extract_delta, args=("r3", "r6", "r7", "f1", "f2")),
}


def inputs(t):
    rng = t.rng
    clip = t.alloc(0x30, "clip")
    values = [-10.0, -1.0, -0.0, 0.0, 0.1, 1.0, 10.0,
              float("nan"), float("inf"), -float("inf"), rng.uniform(-20, 20)]
    values = [struct.unpack(">f", struct.pack(">f", value))[0] for value in values]
    t.wf32(clip + 0x0C, rng.choice(values))
    # EvaluateChannel's existing bool lift and its original both return 0/1.
    for off in (0x20, 0x24):
        t.w32(clip + off, rng.choice([0, 1]))
    t.w32(clip + 0x28, rng.choice([0, 1, 0x100, 0x101, 0xFFFFFFFF]))
    output = t.alloc(32, "output")
    t.args(r3=clip, r4=rng.getrandbits(32), r5=rng.getrandbits(32),
           r6=output, f1=rng.choice(values), f2=rng.choice(values))
