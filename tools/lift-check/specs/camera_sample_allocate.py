"""0x821F9DE8: allocate 40 bytes through the current thread heap, initialize
all fields, and append its pointer even on allocation failure. The shared
operator-new entry executes transparently so its heap-init/Allocate trace must
match the original inline sequence. Includes a heap replacement during init,
byte argument truncation, unrelated bank data and complete write comparison.
"""
from liftcheck.spec import *

FUNCTION = "pongCameraMgr_9DE8_g"
ADDRESS = 0x821F9DE8
SOURCE = "src/game/camera/pong_camera.cpp"
TRIALS = 1000
EXTERNS = {"atFreeList_Alloc": 0x822665C0, "g_sda_base": 0x82600000}


def initialize(c):
    sda = int.from_bytes(c.read(0x82600000, 4), 'big')
    tls = int.from_bytes(c.read(sda, 4), 'big')
    c.write(tls + 4, c.read(tls + 12, 4))


CALLS = {
    "rage_Alloc": run(transparent=True),
    0x820C0038: model(initialize, args=()),
    "heap.vfn_1": model(lambda c: c.ret(r3=int.from_bytes(c.read(c.r(3) + 4, 4), 'big')),
                          args=("r3", "r4", "r5")),
    "atFreeList_Alloc": model(lambda c: c.ret(r3=c.r(3) + 4), args=("r3", "r4")),
}


def inputs(t):
    sda = t.alloc(16, "sda")
    tls = t.alloc(16, "tls")
    heap = t.alloc(8, "heap")
    stale = t.alloc(8, "staleHeap")
    t.w32(sda, tls)
    t.w32(tls + 4, stale)
    t.w32(tls + 12, heap)
    t.w32(heap, t.vtable("heap", 2))
    t.w32(heap + 4, t.rng.choice([0, t.alloc(48, "sample")]))
    t.w32(stale, t.vtable("staleHeap", 2))
    t.w32(0x82600000, sda)
    t.args(r3=t.alloc(32, "bank"), r4=t.u32(), r5=t.u32(),
           r6=t.u32(), r7=t.u32(), r13=sda)
