"""gmPracticeTarget::Construct (0x82112B58).

The allocator is modelled as in match_practice_target_fx_construct: the
original's inlined `new` (0x820C0038 + slot 1 of (*r13)[1]) against the lift's
host helper rage::rage_alloc_aligned, both left out of the call trace. The
block comes back filled with 0xC5 so the `flags &= 0x3F` is visible.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmPracticeTarget::Construct"
ADDRESS = 0x82112B58
SOURCE = "src/game/match/pong_match.cpp"

HOST_ALLOC = 0x82000100   # stand-in address for the host helper (not code)
EXTERNS = {
    "rage::rage_alloc_aligned": HOST_ALLOC,
    "gmPracticeTarget_LayOutTableGrid": 0x821132B0,
}

_trial = {"fail": 0, "orig": 0, "lift": 0}


def _allocate(size, align, ctx):
    assert (size, align) == (0x14, 16), f"allocation of {size:#x} aligned {align}"
    k = _trial[ctx.side]
    _trial[ctx.side] = k + 1
    if (_trial["fail"] >> k) & 1:
        ctx.ret(r3=0)
        return
    p = ctx.alloc(size)
    ctx.write(p, b"\xC5" * size)
    ctx.ret(r3=p)


CALLS = {
    0x820C0038: stub(ret="void"),        # sysMemAllocator_InitMainThread
    0x82113D10: stub(ret="void"),        # gmPracticeTargetFx::Construct(this + 0x24 / + 0x34)
    # Lays out the table grid. It never touches r3, so the original returns
    # `this` through it (its `bl` is the last thing before the epilogue): run it.
    0x821132B0: run(),
    "allocator.vfn_1": model(lambda c: _allocate(c.r(4), c.r(5), c), transparent=True),
    HOST_ALLOC: model(lambda c: _allocate(c.r(3), c.r(4), c), transparent=True),
}


def inputs(t):
    _trial.update(fail=t.rng.choice([0, 0, 0, 1]), orig=0, lift=0)
    tls = t.alloc(0x10, "tls", fill="zero")
    table = t.alloc(0x10, "tlsTable", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(allocator, t.vtable("allocator", 4))
    t.w32(table + 4, allocator)
    t.w32(tls, table)
    dims = t.alloc(0x20, "tableDims")            # *(0x8271A304): +0x10, +0x18 used
    t.floats(dims, 8, 0.5, 3.0)
    t.w32(0x8271A304, dims)
    target = t.alloc(0x70, "target", ctype="gmPracticeTarget")
    t.args(r3=target, r13=tls)
