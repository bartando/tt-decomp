from liftcheck.spec import *

FUNCTION = "rage_free"
ADDRESS = 0x820C00C0
SOURCE = "src/crt/heap.c"
TRIALS = 1000
CALLS = {
    "rage_FindSingleton": stub(ret=lambda c: c.rng.choice((0, 1, 0x100, 0x101, 0xffffff00))),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}
EXTERNS = {"rage_FindSingleton": 0x820F90D0, "g_sda_base": 0x82600000}
RET = None


def inputs(t):
    sda = t.alloc(0x110, "sda")
    tls = t.alloc(16, "tls")
    heap = t.alloc(16, "heap")
    t.w32(heap, t.vtable("heap"))
    t.w32(tls + 4, heap)
    t.w32(sda, tls)
    t.w32(t.sym("g_sda_base"), sda)
    t.args(r3=t.rng.choice((0, t.alloc(32, "block"))), r13=sda)
