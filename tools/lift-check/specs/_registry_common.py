"""Shared setup for the atRegistryEntry specs (not a spec)."""
from liftcheck.spec import stub


def heap_tls(t):
    """r13 block whose TLS allocator (slot 2 = Free) is a fake vtable."""
    sda = t.alloc(0x20, "sda", fill="zero")
    tls = t.alloc(0x10, "tls", fill="zero")
    heap = t.alloc(0x10, "heap")
    t.w32(heap, t.vtable("heap"))
    t.w32(tls + 4, heap)
    t.w32(sda, tls)
    return sda


FREE_CALLS = {
    0x820F90D0: stub(ret=lambda c: c.ret(r3=c.rng.choice([0, 1]))),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}
