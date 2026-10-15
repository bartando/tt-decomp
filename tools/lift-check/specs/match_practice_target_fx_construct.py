"""gmPracticeTargetFx::Construct (0x82113D10): no texture, height offset 0.001,
two zeroed 16-byte colours from the current allocator.

The original inlines `new`: 0x820C0038, then slot 1 (Allocate(size, align)) of
the allocator at (*r13)[1]. The lift calls the host helper
rage::rage_alloc_aligned(size, align) instead, which has no original address.
Both are modelled as the same allocator and left out of the call trace; the
calls to 0x820C0038 stay in it, and the sizes are checked in the models.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmPracticeTargetFx::Construct"
ADDRESS = 0x82113D10
SOURCE = "src/game/match/pong_match.cpp"

HOST_ALLOC = 0x82000100   # stand-in address for the host helper (not code)
EXTERNS = {"rage::rage_alloc_aligned": HOST_ALLOC}


# Which allocations fail (bit k = the k-th one), drawn per trial; the two sides
# call different targets, so their per-target random streams can't decide it.
_trial = {"fail": 0, "orig": 0, "lift": 0}


def _allocate(size, align, ctx):
    assert (size, align) in EXPECT, f"allocation of {size:#x} aligned {align}"
    k = _trial[ctx.side]
    _trial[ctx.side] = k + 1
    ctx.ret(r3=0 if (_trial["fail"] >> k) & 1 else ctx.alloc(size))


EXPECT = {(0x10, 16)}


CALLS = {
    0x820C0038: stub(ret="void"),                                            # sysMemAllocator_InitMainThread
    "allocator.vfn_1": model(lambda c: _allocate(c.r(4), c.r(5), c), transparent=True),
    HOST_ALLOC: model(lambda c: _allocate(c.r(3), c.r(4), c), transparent=True),
}


def tls_allocator(t):
    """r13 -> {table}, table[1] -> allocator with a fake vtable."""
    tls = t.alloc(0x10, "tls", fill="zero")
    table = t.alloc(0x10, "tlsTable", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(allocator, t.vtable("allocator", 4))
    t.w32(table + 4, allocator)
    t.w32(tls, table)
    return tls


def inputs(t):
    _trial.update(fail=t.rng.choice([0, 0, 1, 2, 3]), orig=0, lift=0)
    fx = t.alloc(0x10, "fx", ctype="gmPracticeTargetFx")
    t.args(r3=fx, r13=tls_allocator(t))
