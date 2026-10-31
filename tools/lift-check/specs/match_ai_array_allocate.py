"""Allocate size saturation, capacity truncation, failure, and untouched count."""
from liftcheck.spec import *
from specs.camera_sample_allocate import initialize
FUNCTION = "game_DB80"
ADDRESS = 0x821EDB80
SOURCE = "src/game/match/match_ai_array.cpp"
TRIALS = 256

CALLS = {
    "rage_Alloc": run(transparent=True),
    0x820C0038: model(initialize, args=()),
    "heap.vfn_1": model(lambda c: c.ret(r3=int.from_bytes(c.read(c.r(3) + 4, 4), "big")),
                        args=("r3", "r4", "r5")),
}

def inputs(t):
    sda = t.alloc(16, "sda")
    tls = t.alloc(16, "tls")
    heap = t.alloc(8, "heap")
    stale = t.alloc(8, "stale heap")
    t.w32(sda, tls)
    t.w32(tls + 4, stale)
    t.w32(tls + 12, heap)
    t.w32(heap, t.vtable("heap", 2))
    t.w32(heap + 4, 0 if t.index % 3 == 0 else t.alloc(32, "pointer storage"))
    t.w32(stale, t.vtable("staleHeap", 2))
    t.w32(0x82600000, sda)
    capacity = [0, 1, 65535, 65536, 0x3FFFFFFF, 0x40000000,
                0xFFFFFFFF, t.rng.getrandbits(32)][t.index % 8]
    t.args(r3=t.alloc(16, "array"), r4=capacity, r13=sda)
