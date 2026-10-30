"""Animation pointer array append, including resource-aware construction and freeing.

Growth cases avoid capacity wrap and allocation failure when old entries exist:
those make the original copy out of bounds or through a null pointer.
"""
from liftcheck.spec import alloc, model, stub

FUNCTION = "rage::crAnimPointerArray_AppendSlot"
ADDRESS = 0x8224DE98
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
EXTERNS = {"g_sda_base": 0x82600000}


def construct(ctx):
    # Nonzero, position-dependent constructor effects expose missing or misplaced calls.
    address = ctx.r(3)
    ctx.write(address, (address ^ 0xA53C7E19).to_bytes(4, "big"))
    ctx.ret()


CALLS = {
    0x820DEC88: alloc(size_reg="r3"),
    0x8224DFC0: model(construct, args=("r3",)),
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
    count = rng.choice([0, 1, 2, 7, 16, 31, 255, 65535])
    grow = count != 65535 and rng.choice([True, False])
    capacity = count if grow else (count + 1) & 0xffff
    growth = rng.choice([1, 2, 3, 16, 0x10001, 0xFFFF0010])
    array = t.alloc(8, "array")
    data = 0 if count == 0 and grow and rng.choice([True, False]) else t.alloc(4 * (count + 1), "data")
    t.w32(array, data)
    t.w16(array + 4, count)
    t.w16(array + 6, capacity)
    t.args(r3=array, r4=growth, r13=sda)
