"""Append a 16-bit slot, including growth, copying and both allocator-free paths.

Growth cases stay below capacity 65520: 16-bit capacity wrap would allocate a
smaller block than the existing data and the original then writes out of bounds.
Allocation failures are not modeled; the original assumes allocation succeeds.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "grmU16Array_AppendSlot"
ADDRESS = 0x82378040
SOURCE = "src/rage/rage_grm.cpp"
EXTERNS = {"g_sda_base": 0x82600000}
CALLS = {
    0x820DEC88: alloc(size_reg="r3"),
    0x820F90D0: stub(ret=lambda c: c.rng.choice([0, 1, 0x100, 0x101])),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    sda = t.alloc(8, "sda", fill="zero")
    thread = t.alloc(8, "thread", fill="zero")
    heap = t.alloc(4, "heap")
    t.w32(sda, thread)
    t.w32(thread + 4, heap)
    t.w32(heap, t.vtable("heap"))
    t.w32(0x82600000, sda)
    count = rng.choice([0, 1, 15, 16, 17, 31, 32, 255, 65535])
    grow = count != 65535 and rng.choice([True, False])
    capacity = count if grow else (count + 1) & 0xffff
    array = t.alloc(8, "array")
    data = 0 if count == 0 and grow and rng.choice([True, False]) else t.alloc(2 * (count + 1), "data")
    t.w32(array, data)
    t.w16(array + 4, count)
    t.w16(array + 6, capacity)
    t.args(r3=array, r4=rng.getrandbits(32), r13=sda)
