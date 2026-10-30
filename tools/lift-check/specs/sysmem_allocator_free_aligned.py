from liftcheck.spec import *

FUNCTION = "sysMemAllocator_FreeAligned"
ADDRESS = 0x82186228
SOURCE = "src/rage/memory/rage_heap.c"
TRIALS = 1000
RET = None
EXTERNS = {"g_sda_base": 0x82600000, "rage_FindSingleton": 0x820F90D0,
           "rage_free": 0x820C00C0}
CALLS = {
    "heap.vfn_17": stub(ret=lambda c: c.rng.choice((0, 1, 0x100, 0x101)), args=("r3",)),
    "rage_FindSingleton": stub(ret=lambda c: c.rng.choice((0, 1, 0x100, 0x101))),
    "rage_free": stub(ret="void", args=("r3",)),
}


def inputs(t):
    sda = t.alloc(16, "sda")
    tls = t.alloc(8, "tls")
    heap = t.alloc(4, "heap")
    block = t.alloc(32, "block")
    t.w32(heap, t.vtable("heap", slots=18))
    t.w32(tls + 4, heap)
    t.w32(sda, tls)
    t.w32(t.sym("g_sda_base"), sda)
    t.w32(block, t.u32())
    t.args(r3=t.rng.choice((0, block + 4)), r13=sda)
