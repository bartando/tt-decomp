"""0x820DBBF8: reversal, normalized layers, failures and all defined VMX lanes.

Trials index % 8 == 1 deterministically fail the first recursive sample. The
original then reads an uninitialized temporary w; ignore only output+12..+15
on those trials. Its xyz, call trace and all other bytes remain checked.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_BBF8_g"
ADDRESS = 0x820DBBF8
SOURCE = "src/anim/root_motion_blend.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def extract(ctx):
    status = int.from_bytes(ctx.read(ctx.r(3) + 0x24, 4), "big")
    if status & 0xFF:
        values = [ctx.rng.choice([0.0, -0.0, 1e-40, -1e-40, ctx.rng.uniform(-10, 10)]) for _ in range(8)]
        ctx.write(ctx.r(6), struct.pack(">8f", *values))
    ctx.ret(r3=status)


CALLS = {
    0x820DBA60: run(),
    0x820DBB48: run(),
    0x82248C58: model(extract, args=("r3", "r6", "f1", "f2")),
    0x8240E6D0: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    layers = t.alloc(0x70, "layers")
    n = rng.randrange(1, 4)
    reverse = t.index % 4 == 1
    reverse_failure = t.index % 8 == 1
    for i in range(3):
        clip = t.alloc(0x28, f"clip{i}")
        t.wf32(clip + 0x0C, rng.choice([0.0, -1.0, 1.0, float("nan"), rng.uniform(0, 5)]))
        name = f"clip{i}".encode() + b"\0"
        t.w32(clip + 0x20, t.alloc(len(name), f"clip{i}.name", fill=name))
        status = 0x100 if reverse_failure else 1 if reverse else rng.choice([0, 1, 0x100, 0x101, 0xFFFFFFFF])
        t.w32(clip + 0x24, status)
        t.w32(layers + 0x10 + 4 * i, clip if i < n else 0)
        t.wf32(layers + 0x1C + 4 * i, rng.choice([0.0, -0.5, 0.1, 1.0, float("nan")]))
    # Guarantee an initial positive normalized layer, while still allowing zero
    # leading weights and skipped later layers.
    first = rng.randrange(n)
    for i in range(first):
        t.wf32(layers + 0x1C + 4 * i, 0.0)
    t.wf32(layers + 0x1C + 4 * first, 1.0)
    output = t.alloc(16, "output", floats=[(0, 4)])
    if reverse_failure:
        t.ignore(output + 12, 4)
    if reverse:
        start, end = 1.0, -0.25
    else:
        start, end = rng.choice([(0.0, 1.0), (-1.0, 2.0), (0.5, 0.5), (float("nan"), 1.0), (0.0, float("nan"))])
    t.args(r3=output, r4=layers, f1=start, f2=end)
