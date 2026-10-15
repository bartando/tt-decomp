"""rage::sysMemSimpleAllocator::SetBreakAllocIndex (0x82186D98)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::SetBreakAllocIndex"
ADDRESS = 0x82186D98
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj, r4=t.rng.getrandbits(32))
