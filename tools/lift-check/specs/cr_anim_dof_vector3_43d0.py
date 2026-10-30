"""0x820C43D0: vector channel dispatch.

Exercise all high flag nibbles and low bits, both callback slots, partial
writes, and array replacement after either of the first two scalar callbacks.
Compare call targets, time/output arguments, and all writes.

Limits: callbacks are boundary models. Active channels are non-null, the output
is an aligned, disjoint vec3, and replaced arrays remain valid. r4 is an unused
ABI slot, so only r3/f1/r5 are compared at callback boundaries. Float equality
ignores NaN payloads and zero signs; FP status flags and traps are outside scope.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::EvaluateChannels"
ADDRESS = 0x820C43D0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000
FP_CONTRACT = "off"


def _u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def _evaluate(ctx, count):
    channel = ctx.r(3)
    if _u32(ctx, channel + 0x20):
        ctx.write(ctx.r(5), ctx.read(channel + 4, 4 * count))
    replacement = _u32(ctx, channel + 0x18)
    if replacement:
        ctx.write(_u32(ctx, channel + 0x14) + 4, struct.pack(">I", replacement))
    ctx.write(channel + 0x1C, struct.pack(">I", _u32(ctx, channel + 0x1C) + 1))


CALLS = {
    "channel.vfn_3": model(lambda c: _evaluate(c, 3), args=("r3", "f1", "r5")),
    "channel.vfn_5": model(lambda c: _evaluate(c, 1), args=("r3", "f1", "r5")),
}


def inputs(t):
    rng = t.rng
    owner = t.alloc(8, "channelData")
    output = t.alloc(12, "output")
    t.floats(output, 3, -10, 10)
    mode = rng.choice((0, 0, 0x10, 0x10, rng.randrange(2, 16) << 4))
    t.w8(owner + 1, mode | rng.randrange(16))
    t.w32(owner + 4, 0)
    if mode <= 0x10:
        table = t.vtable("channel")
        arrays = [t.alloc(12, f"channels{bank}") for bank in range(2)]
        t.w32(owner + 4, arrays[0])
        replace_at = rng.choice((-1, 0, 1))
        for bank, array in enumerate(arrays):
            for index in range(3):
                channel = t.alloc(0x24, f"channel{bank}_{index}")
                t.w32(array + 4 * index, channel)
                t.w32(channel, table)
                for lane in range(3):
                    t.wf32(channel + 4 + 4 * lane, rng.uniform(-100, 100))
                t.w32(channel + 0x14, owner)
                t.w32(channel + 0x18, arrays[1] if bank == 0 and index == replace_at else 0)
                t.w32(channel + 0x1C, 0)
                t.w32(channel + 0x20, rng.choice((0, 1, 1, 1)))
    time = rng.choice((0.0, -0.0, 1.0, rng.uniform(-100, 100)))
    t.args(r3=owner, r4=rng.getrandbits(32), r5=output, f1=time)
