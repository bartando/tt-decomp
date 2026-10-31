"""Count/flags before heap init, capacity rereads, index fill, then shuffle."""
from liftcheck.spec import *
from specs.camera_sample_allocate import initialize
FUNCTION = "gmPracticeTargetWordArray_Init"
ADDRESS = 0x821B2A58
SOURCE = "src/game/match/practice_target_words.cpp"
TRIALS = 256

def allocate(ctx):
    heap = ctx.r(3)
    array = int.from_bytes(ctx.read(heap + 8, 4), "big")
    ctx.write(heap + 16, ctx.read(array + 4, 4))
    flags = ctx.read(array + 16, 1)[0]
    ctx.write(heap + 20, bytes([flags]))
    ctx.write(array + 16, bytes([flags ^ 0x15]))
    ctx.write(array + 8, ctx.read(heap + 12, 4))
    ctx.ret(r3=int.from_bytes(ctx.read(heap + 4, 4), "big"))

def shuffle(ctx):
    array = ctx.r(3)
    capacity = int.from_bytes(ctx.read(array + 8, 4), "big", signed=True)
    data = int.from_bytes(ctx.read(array, 4), "big")
    if capacity > 0:
        actual = ctx.read(data, capacity * 4)
        expected = b"".join(i.to_bytes(4, "big") for i in range(capacity))
        assert actual == expected, "index pool was not filled before shuffling"
    ctx.write(array + 12, b"\0" * 4)

CALLS = {
    "rage_Alloc": run(transparent=True),
    0x820C0038: model(initialize, args=()),
    "heap.vfn_1": model(allocate, args=("r3", "r4", "r5")),
    "gmPracticeTargetWordArray_Shuffle": model(shuffle, args=("r3",), deref={"r3": 20}),
}

def inputs(t):
    array = t.alloc(32, "word array")
    sda = t.alloc(16, "sda")
    tls = t.alloc(16, "tls")
    heap = t.alloc(32, "heap")
    stale = t.alloc(8, "stale heap")
    t.w32(sda, tls)
    t.w32(tls + 4, stale)
    t.w32(tls + 12, heap)
    t.w32(heap, t.vtable("heap", 2))
    t.w32(heap + 4, t.alloc(16 * 4, "indices"))
    t.w32(heap + 8, array)
    t.w32(heap + 12, t.rng.choice([0, 1, 4, 16]))
    t.w32(stale, t.vtable("staleHeap", 2))
    t.w32(0x82600000, sda)
    capacity = [0, 1, 4, 16, 0x3FFFFFFF, 0x40000000, 0xFFFFFFFF][t.index % 7]
    t.args(r3=array, r4=capacity, r5=t.index % 2, r6=(t.index // 2) % 2, r13=sda)
