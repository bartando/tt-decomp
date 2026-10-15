"""TriStrip::TriStrip: two rage operator new[] calls through the TLS allocator."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStrip::TriStrip"
ADDRESS = 0x821342A0
SOURCE = "src/game/misc/cm_operators.cpp"
RET = None   # the original returns `this` in r3; a C++ ctor returns nothing

CALLS = {
    "alloc.vfn_1": alloc(size_reg="r4"),
}


def tls_allocator(t):
    """r13 -> block whose word 0 is the thread block; thread block +4 -> allocator.
    The lift reads r13 through g_sda_base (0x82600000), so that word points at the
    same block."""
    r13 = t.alloc(0x40, "r13", fill="zero")
    thread = t.alloc(0x40, "thread", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(r13, thread)
    t.w32(thread + 4, allocator)
    t.w32(allocator, t.vtable("alloc"))
    t.w32(0x82600000, r13)
    t.args(r13=r13)


def inputs(t):
    rng = t.rng
    tls_allocator(t)
    strip = t.alloc(0x18, "strip")
    big = rng.random() < 0.2
    n_tris = rng.choice([0x40000000, 0x80000000, 0xFFFFFFFF]) if big else rng.randrange(1, 300)
    n_idx = rng.choice([0x80000000, 0xFFFFFFFF]) if big else rng.randrange(1, 600)
    t.args(r3=strip, r4=n_tris, r5=n_idx)
