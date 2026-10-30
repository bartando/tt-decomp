"""Scalar lerp: t is port +12, endpoints +20/+28; strict near-endpoint tests.

Execute the original port evaluator, with direct/unconnected/virtual inputs.
Trace lazy evaluation and reversed endpoint call order; virtual inputs count
reads. Include exact epsilon boundaries and adjacent floats, extrapolation,
NaN/Inf, signed zero, subnormals and cancellation-sensitive FMA operands.
Compare all writes/calls/registers exactly, with guarded output. Limits: quiet
NaNs/default FP environment, readable synthetic nodes, boundary-model upstream
GetFloat methods; no signaling NaNs, payload/zero-sign proof or game replay.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::cmLerp::GetFloat"
ADDRESS = 0x8227BA78
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1000
RET = None


def get_float(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 4, 4))
    count = int.from_bytes(ctx.read(ctx.r(3) + 8, 4), "big")
    ctx.write(ctx.r(3) + 8, struct.pack(">I", count + 1))


CALLS = {
    0x82179350: run(),
    "input.vfn_4": model(get_float, args=("r3", "r4")),
}


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def inputs(t):
    rng = t.rng
    node = t.alloc(40, "lerp")
    output = t.alloc(12, "outputWithGuards", floats=[4]) + 4
    table = t.vtable("input", slots=5)
    times = [0, 0x80000000, 1, 0x80000001, 0x3F000000, 0x3F800000,
             0xBF800000, 0x40000000, 0x7F800000, 0xFF800000, 0x7FC12345]
    for boundary in (0x38D1B717, 0xB8D1B717, 0x3F7FF972, 0x3F800347):
        times.extend((boundary - 1, boundary, boundary + 1))
    factor = rng.choice([f32(bits) for bits in times] + [rng.uniform(-2, 2)])
    endpoints = (0.0, -0.0, 1.0, -1.0, 1e20, -1e20, f32(1), f32(0x807FFFFF),
                 float("nan"), float("inf"), -float("inf"), rng.uniform(-1e6, 1e6))
    a, b = rng.choice(endpoints), rng.choice(endpoints)
    if rng.randrange(4) == 0:
        # Product rounded separately loses the small nonzero fused result.
        factor, a, b = f32(0x3F000001), -1.0, f32(0x3F7FFFFE)
    for index, value in enumerate((factor, a, b)):
        data = t.alloc(16, f"input{index}", floats=[4])
        kind = rng.choice((1, 2, 2)) if index == 0 else rng.choice((0, 1, 2, 2, 0xFFFFFFFF))
        t.w32(node + 12 + index * 8, data if kind in (1, 2) else 0)
        t.w32(node + 16 + index * 8, kind)
        if kind == 2:
            t.w32(data, table)
            t.wf32(data + 4, value)
            t.w32(data + 8, 0)
        else:
            t.wf32(data, value)
    t.args(r3=node, r4=output)
