"""Install the default 44 MiB thread heap once, preserving an active heap.

Exercise all combinations of active slot and static initialization bit, with
independent saved-slot contents and unrelated flag bits. The constructor model checks
that the static guard is published before construction; memory and call diffs
check the slots, constructor arguments and exit callback.
"""
from liftcheck.spec import model

FUNCTION = "sysMemAllocator_InitThreadHeap"
ADDRESS = 0x820C0038
SOURCE = "src/crt/entry.c"
TRIALS = 1200
EXTERNS = {"g_sda_base": 0x82600000}


def construct(ctx):
    assert int.from_bytes(ctx.read(0x8271B1D8, 4), "big") & 1
    # Give constructor output observable effects without allocating 44 MiB.
    ctx.write(ctx.r(3), ctx.rng.randbytes(0xC4))


CALLS = {
    "xe_alloc_thread_ctx_6CA8": model(construct, args=("r3", "r4", "r5")),
    "atexit": model(lambda c: c.ret(r3=c.rng.choice([0, -1, 1])), args=("r3",)),
}


def inputs(t):
    sda = t.alloc(16, "tlsRoot")
    thread = t.alloc(24, "allocatorSlotsAndGuards")
    t.w32(sda, thread)
    t.w32(0x82600000, sda)
    t.w32(thread + 4, t.rng.choice([0, 0, t.alloc(16, "existingHeap")]))
    t.w32(thread + 8, t.rng.getrandbits(32))
    t.w32(0x8271B1D8, t.rng.choice([0, 1, 2, 3, 0xFFFFFFFE, 0xFFFFFFFF,
                                             t.rng.getrandbits(32)]))
    t.put(0x8271B114, t.rng.randbytes(0xC4))
    t.args(r13=sda)
