"""pongNetMessageHolder::CleanupInternalArray (0x823C3878): if +8 is set, store
0x8206C304 into its two 12-byte elements (+0xC, then +0), free it, clear +8."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongNetMessageHolder::CleanupInternalArray"
ADDRESS = 0x823C3878
SOURCE = "src/game/network/pong_network.cpp"
RET = None

EXTERNS = {"sysMemAllocator_Free": 0x820C00C0}   # the name is marked with two addresses
CALLS = {"sysMemAllocator_Free": stub(ret="void", args=("r3",))}


def inputs(t):
    obj = t.alloc(0x10, "holder")
    t.w32(obj + 8, 0 if t.rng.random() < 0.3 else t.alloc(0x20, "array"))
    t.args(r3=obj)
