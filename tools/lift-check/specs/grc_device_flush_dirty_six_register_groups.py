"""Six-register dirty runs and the final GPU packet.

Limits: the caller supplies a nonzero mask confined to the upper 32 bits;
source and command buffers are aligned and disjoint. Overflow and rollover
are modeled, including their arguments and returned cursors, but their own
buffer management and packet emission are not exercised.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_FlushDirtySixRegisterGroups"
ADDRESS = 0x82362718
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 500
RET = None


def overflow(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 12, 4), "big"))


def rollover(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 16, 4), "big"))


CALLS = {
    "grcDevice_WriteRegisterRunOverflow": model(
        overflow, args=("r3", "r4", "r5", "r6", "r7", "r8"), deref={"r6": 4}),
    "rage_A980": model(rollover, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    state = t.alloc(20, "device", fill="zero")
    output = t.alloc(4096, "commands")
    replacement = t.alloc(4096, "overflow_commands")
    final = t.alloc(4096, "rollover_commands")
    values = t.alloc(32 * 24 + 4, "values") + 4
    cursor = output + rng.choice([16, 20])
    t.w32(state, cursor)
    t.w32(state + 4, cursor + 4 * rng.choice([1, 7, 8, 13, 49, 193, 300]))
    t.w32(state + 8, rng.choice([cursor, output + 4000, replacement + 4000, 0xFFFFFFFF]))
    t.w32(state + 12, replacement + rng.choice([16, 20]))
    t.w32(state + 16, final + 16)
    start = rng.randrange(32)
    length = rng.randrange(1, 33 - start)
    mask = rng.choice([1, 1 << 31, 0xFFFFFFFF, 0x80000001, 0xAAAAAAAA,
                       rng.getrandbits(32) or 1, ((1 << length) - 1) << start]) << 32
    if rng.randrange(8) == 0:
        # One in-buffer run ends exactly at the rollover threshold.
        mask = 1 << 63
        t.w32(state + 4, cursor + 128)
        t.w32(state + 8, cursor + (cursor & 7) + 28)
    t.args(r3=state, r4=mask, r5=rng.getrandbits(32), r6=values)
