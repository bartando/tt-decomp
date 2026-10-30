"""HSM helpers use live singleton/name slots, with stores relative to their owners."""
from liftcheck.spec import *

FUNCTION = "jumptable_5C20"
ADDRESS = 0x821C5C20
SOURCE = "src/rage/core/hsm.cpp"
CALLS = {0x82222800: stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    obj = t.alloc(0x12800, "object")
    hsm = t.alloc(0x1500, "hsm")
    name = t.pick([b"", b"settings", b"x" * 60])
    names = t.alloc(128, "names", fill=(bytes(45) + name + b"\0").ljust(128, b"\0"))
    t.w32(obj + 532, t.pick([0, 1, 4, 255, t.u32()]))
    t.w32(0x8271A7C0, hsm)
    t.w32(0x8271A7C4, names)
    t.args(r3=obj)
