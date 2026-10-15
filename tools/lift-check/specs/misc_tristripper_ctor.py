"""TriStripper::TriStripper: allocates the adjacency arrays and links every edge
(LinkEdge runs as the original on both sides)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStripper::TriStripper"
ADDRESS = 0x82135648
SOURCE = "src/game/misc/cm_operators.cpp"
RET = None   # the original returns `this`

CALLS = {
    "alloc.vfn_1": alloc(size_reg="r4"),
    0x821354D0: run(),      # TriStripper::LinkEdge
}


def tls_allocator(t):
    r13 = t.alloc(0x40, "r13", fill="zero")
    thread = t.alloc(0x40, "thread", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(r13, thread)
    t.w32(thread + 4, allocator)
    t.w32(allocator, t.vtable("alloc"))
    t.w32(0x82600000, r13)          # the lift's g_sda_base
    t.args(r13=r13)


def inputs(t):
    rng = t.rng
    tls_allocator(t)
    n = rng.choice([0, 1, 2, 5, 12, 30])
    nv = rng.choice([4, 6, 12])
    idx = t.alloc(6 * max(n, 1), "indices")
    for k in range(n):
        for j, v in enumerate(rng.sample(range(nv), 3)):
            t.w16(idx + 6 * k + 2 * j, v)
    s = t.alloc(0x10, "stripper")
    t.args(r3=s, r4=n, r5=idx)
