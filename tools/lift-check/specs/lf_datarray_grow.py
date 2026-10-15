"""atArray<u32>::Realloc (0x821322B0, called datArray_Grow): new block, copy min(count, cap), free old."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from player_common import inlined

FUNCTION = "datArray_Grow"
ADDRESS = 0x821322B0
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {
    0x820DEC88: alloc(size_reg="r3"),
    0x820C00C0: inlined(),                       # rage_free, inlined in the original
    0x820F90D0: stub(ret=lambda c: c.ret(r3=c.rng.choice([0, 1]))),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    count = rng.choice([0, 1, 3, 7])
    cap = rng.choice([0, 1, 2, 4, 9, 0x100])
    arr = t.alloc(12, "array")
    t.w32(arr, t.alloc(4 * max(count, 1), "old") if count or rng.random() < 0.7 else 0)
    t.w32(arr + 4, count)
    t.w32(arr + 8, rng.choice([count, count + 3]))
    sda = t.alloc(0x20, "sda", fill="zero")
    tls = t.alloc(0x10, "tls", fill="zero")
    heap = t.alloc(0x10, "heap")
    t.w32(heap, t.vtable("heap"))
    t.w32(tls + 4, heap)
    t.w32(sda, tls)
    t.args(r3=arr, r4=cap, r13=sda)
