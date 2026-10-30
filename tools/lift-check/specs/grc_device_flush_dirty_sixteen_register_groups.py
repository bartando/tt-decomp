"""Sixteen-register dirty runs, alignment padding and overflow.

Callers supply nonzero masks and aligned, disjoint source and command buffers.
Overflow arguments and the returned cursor are checked; its own packet emission
is modeled. The adapter maps Xenon's single-GPR uint64 argument to PPC32's pair.
"""
from liftcheck.spec import *

FUNCTION = "liftcheck_dirty_sixteen_adapter"
ADDRESS = 0x82362858
SOURCE = "tools/lift-check/specs/grc_device_flush_dirty_sixteen_register_groups_adapter.cpp"
TRIALS = 500
RET = None


def overflow(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 8, 4), "big"))


CALLS = {"grcDevice_WriteRegisterRunOverflow": model(
    overflow, args=("r3", "r4", "r5", "r6", "r7", "r8"), deref={"r6": 4})}


def inputs(t):
    rng = t.rng
    state = t.alloc(12, "device", fill="zero")
    output = t.alloc(8192, "commands")
    replacement = t.alloc(8192, "replacement")
    values = t.alloc(4096 + 16, "values") + 16
    cursor = output + rng.choice([16, 20, 24, 28])
    t.w32(state, cursor)
    t.w32(state + 4, cursor + 4 * rng.choice([1, 18, 19, 20, 35, 64, 256, 1027, 1500]))
    t.w32(state + 8, replacement + rng.choice([16, 20, 24, 28]))
    start = rng.randrange(64)
    length = rng.randrange(1, 65 - start)
    mask = rng.choice([1, 1 << 63, (1 << 64) - 1, 0xFFFFFFFF00000000,
                       0x00000000FFFFFFFF, 0x8000000180000001,
                       0xAAAAAAAAAAAAAAAA, rng.getrandbits(64) or 1,
                       ((1 << length) - 1) << start])
    t.args(r3=state, r4=mask, r5=rng.choice([0x4000, 0x4400]), r6=values)
