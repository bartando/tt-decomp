"""0x820C44A0: quaternion channel evaluation (despite the capsule symbol name).

Cover all flag nibbles, ignored low bits, whole-quaternion slot 4, scalar
slot 5, four-channel normalization, and three-channel w reconstruction on
both sides of |xyz|^2 == 1. Include zero/signed zero, non-unit results,
rounding boundaries, NaNs and infinities, partial channel writes, and channel
array replacement during callbacks. Compare all writes and call arguments;
execute the original normalization and double-precision sqrt callees.

Limits: virtual channel bodies are boundary models, not proofs of their
implementations. Active channels are non-null and output is a disjoint,
aligned vec4. Callbacks may replace the array but do not delete its storage.
Subnormals, signaling NaNs, FP status flags and traps are outside scope.
r4 is an unused ABI slot; only r3/f1/r5 are meaningful at the virtual call
boundary. Harness float equality ignores NaN payloads and zero signs.
No ignored memory, patched code, or floating-point tolerance.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::crAnimDofQuaternion::EvaluateChannels"
ADDRESS = 0x820C44A0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000


def _u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def _evaluate(ctx, count):
    channel = ctx.r(3)
    # A channel may leave its output untouched, so preexisting output matters.
    if _u32(ctx, channel + 0x24):
        ctx.write(ctx.r(5), ctx.read(channel + 4, 4 * count))
    owner = _u32(ctx, channel + 0x14)
    replacement = _u32(ctx, channel + 0x18)
    if replacement:
        ctx.write(owner + 4, struct.pack(">I", replacement))
    visits = _u32(ctx, channel + 0x1C)
    ctx.write(channel + 0x1C, struct.pack(">I", visits + 1))


CALLS = {
    "channel.vfn_4": model(lambda c: _evaluate(c, 4), args=("r3", "f1", "r5")),
    "channel.vfn_5": model(lambda c: _evaluate(c, 1), args=("r3", "f1", "r5")),
    0x820C42D8: run(),
    0x824301D0: run(),
}


def inputs(t):
    rng = t.rng
    owner = t.alloc(8, "channelData")
    output = t.alloc(16, "output")
    t.floats(output, 4, -2, 2)
    mode = rng.choice((0, 0, 0x10, 0x10, 0x20, 0x20, rng.randrange(3, 16) << 4))
    t.w8(owner + 1, mode | rng.randrange(16))
    # Unknown nibbles must return without dereferencing the array.
    t.w32(owner + 4, 0)
    if mode <= 0x20:
        values = list(rng.choice((
            (0, 0, 0, 0), (-0.0, 0, -0.0, -0.0),
            (0, 0, 0, 1), (1, 0, 0, 0), (-1, 0, 0, 0),
            (0.6, 0.8, 0, -1), (0.25, -0.5, 0.125, 9),
            (1 - 2**-24, 0, 0, -3), (1 + 2**-23, 0, 0, 3),
            (1, 2**-12, 0, -1), (1, 2**-11, 0, 1),
            (float("nan"), 0, 0, 1), (0, float("nan"), 0, 1),
            (0, 0, float("nan"), 1), (0, 0, 0, float("nan")),
            (float("inf"), 0, 0, 1), (0, -float("inf"), 0, 1),
            (0, 0, float("inf"), 1),
            tuple(rng.uniform(-4, 4) for _ in range(4)),
        )))
        table = t.vtable("channel")
        arrays = [t.alloc(16, f"channels{k}") for k in range(2)]
        t.w32(owner + 4, arrays[0])
        replace_at = rng.choice((-1, -1, 0, 1))
        for bank, array in enumerate(arrays):
            for index in range(4):
                channel = t.alloc(0x28, f"channel{bank}_{index}")
                t.w32(array + 4 * index, channel)
                t.w32(channel, table)
                for lane in range(4):
                    value = values[lane] if mode == 0 else values[index]
                    t.wf32(channel + 4 + 4 * lane, value)
                t.w32(channel + 0x14, owner)
                t.w32(channel + 0x18, arrays[1] if bank == 0 and index == replace_at else 0)
                t.w32(channel + 0x1C, 0)
                t.w32(channel + 0x24, rng.choice((0, 1, 1, 1)))
    time = struct.unpack(">f", struct.pack(">f", rng.choice((0, -0.0, 1, rng.uniform(-100, 100)))))[0]
    t.args(r3=owner, r4=rng.getrandbits(32), r5=output, f1=time)
