"""0x820DEC88: operator-new-style TLS allocator entry, with 16-byte alignment.

The entry always initializes the thread allocator, even for a zero-byte request.
The initializer model changes the active heap to catch loading it before init.
"""
from liftcheck.spec import model, stub

FUNCTION = "_Z10rage_Allocj"
ADDRESS = 0x820DEC88
SOURCE = "src/rage/core/rage_core_utils.cpp"
TRIALS = 1200
EXTERNS = {"g_sda_base": 0x82600000}


def initialize(ctx):
    # g_sda_base holds the guest r13 value on the compiled side.
    sda = int.from_bytes(ctx.read(0x82600000, 4), "big")
    tls = int.from_bytes(ctx.read(sda, 4), "big")
    heap = int.from_bytes(ctx.read(tls + 12, 4), "big")
    ctx.write(tls + 4, heap.to_bytes(4, "big"))
    ctx.ret()


def allocate(ctx):
    # No actual large allocation: the wrapper must preserve all 32 size bits.
    heap = ctx.r(3)
    result = int.from_bytes(ctx.read(heap + 4, 4), "big")
    ctx.ret(r3=result)


CALLS = {
    0x820C0038: model(initialize, args=()),
    "heap.vfn_1": model(allocate, args=("r3", "r4", "r5")),
    "heap.vfn_0": stub(args=("r3", "r4", "r5")),
    "heap.vfn_2": stub(args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    sda = t.alloc(32, "sda")
    tls = t.alloc(32, "tls")
    heap = t.alloc(32, "allocator")
    stale_heap = t.alloc(32, "staleAllocator")
    t.w32(heap, t.vtable("heap"))
    t.w32(heap + 4, rng.choice([0, t.alloc(32, "allocation")]))
    t.w32(stale_heap, t.vtable("staleHeap"))
    t.w32(tls + 4, stale_heap)
    t.w32(tls + 8, stale_heap)
    t.w32(tls + 12, heap)
    t.w32(sda, tls)
    t.w32(0x82600000, sda)
    size = rng.choice([0, 1, 4, 15, 16, 17, 32, 63, 64, 65, 255, 4096,
                       0x7fffffff, 0x80000000, 0xffffffff, rng.getrandbits(32)])
    t.args(r3=size, r13=sda)
