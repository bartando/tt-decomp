"""TriStripper::JoinStrips: stitches every strip into one new index list.
TakeBest, Erase and StripVertexCache::Access run as the original on both sides,
so this checks the join itself. Indices avoid 0xFFFF: the stack cache's m_pass
starts as garbage and an index equal to the empty marker would read it."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStripper::JoinStrips"
ADDRESS = 0x82134E90
SOURCE = "src/game/misc/cm_operators.cpp"



class run_cache_head(run):
    """Runs the original; compares only m_hits and m_verts of the cache it gets
    (m_pass/m_setByHit of empty slots are stack garbage, different on each side)."""
    deref = {"r4": 0x28}


CALLS = {
    0x821357B8: run(),      # StripVertexCache::Access
    0x82134C10: run_cache_head(),   # TriStripList::TakeBest
    0x82134350: run(),      # TriStripList::Erase
    0x820C00C0: stub(ret="void"),
    "alloc.vfn_1": alloc(size_reg="r4"),
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
    pool = [rng.randrange(0xFFFF) for _ in range(rng.choice([4, 10, 25, 60]))]
    n = rng.choice([1, 2, 3, 5, 8])
    lst = t.alloc(8, "list", fill="zero")
    items = t.alloc(4 * n, "items")
    for k in range(n):
        s = t.alloc(0x18, f"strip{k}")
        m = rng.randrange(1, 14)
        idx = t.alloc(2 * m, f"strip{k}.indices")
        for j in range(m):
            t.w16(idx + 2 * j, rng.choice(pool))
        t.w32(s + 0x00, rng.choice([0, 1]))
        t.w32(s + 0x04, m)
        t.w32(s + 0x08, t.alloc(4, f"strip{k}.tris"))
        t.w32(s + 0x0C, m)
        t.w32(s + 0x10, idx)
        t.w32(items + 4 * k, s)
    t.w32(lst, items)
    t.w32(lst + 4, n)
    stripper = t.alloc(0x10, "stripper")
    out = t.alloc(4, "outIndices", fill="zero")
    t.args(r3=stripper, r4=lst, r5=out)
