"""atSingleton_vfn_28_DBC8_1 (0x8248DBC8): movie player sample ring buffer."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "atSingleton_vfn_28_DBC8_1"
ADDRESS = 0x8248DBC8
SOURCE = "src/game/misc/ccal_ring_buffer.cpp"

CALLS = {"slot.vfn_1": stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    cap = rng.choice([1, 2, 4, 8])
    rb = t.alloc(0x48, "rb")
    slots = t.alloc(0x3C * cap, "slots")
    vt = t.vtable("slot", 4)
    for k in range(cap):
        t.w32(slots + 0x3C * k, vt)
    t.w32(rb + 0x30, slots)
    t.w32(rb + 0x34, cap)
    t.w32(rb + 0x38, rng.randrange(cap))
    t.w32(rb + 0x3C, rng.randrange(cap))
    t.w32(rb + 0x44, rng.randrange(cap + 1))
    t.args(r3=rb)
