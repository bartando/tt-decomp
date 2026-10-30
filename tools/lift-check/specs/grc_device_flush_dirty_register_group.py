"""GPU register packet runs.

Limits: nonzero masks as guaranteed by callers; aligned, disjoint source and
command buffers; register numbers in the caller's range. Overflow is modelled:
the helper's arguments and input data are checked, and it returns a fresh
cursor, but its own packet emission and buffer management are not exercised.
The checker translates the single-GPR uint64 argument to PPC32's pair.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_FlushDirtyRegisterGroup"
ADDRESS = 0x82362658
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 500
RET = None


def overflow(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 8, 4), "big"))


CALLS = {"grcDevice_WriteRegisterRunOverflow": model(
    overflow, args=("r3", "r4", "r5", "r6", "r7", "r8"), deref={"r6": 4})}


def inputs(t):
    rng = t.rng
    state = t.alloc(12, "device", fill="zero")
    output = t.alloc(4096, "commands")
    replacement = t.alloc(4096, "replacement")
    values = t.alloc(260, "values") + 4
    cursor = output + 16
    t.w32(state, cursor)
    t.w32(state + 4, cursor + 4 * rng.choice([1, 2, 3, 8, 32, 64, 65, 100]))
    t.w32(state + 8, replacement + 16)
    run_start = rng.randrange(64)
    run_length = rng.randrange(1, 65 - run_start)
    mask = rng.choice([1, 1 << 63, (1 << 64) - 1, 0xFFFFFFFF00000000,
                       0x00000000FFFFFFFF, 0x8000000180000001,
                       0xAAAAAAAAAAAAAAAA, rng.getrandbits(64) or 1,
                       ((1 << run_length) - 1) << run_start])
    t.args(r3=state, r4=mask, r5=rng.randrange(0, 0x4000), r6=values)
