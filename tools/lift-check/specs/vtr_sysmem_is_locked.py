"""rage::sysMemSimpleAllocator::IsLocked (0x821878B0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::IsLocked"
ADDRESS = 0x821878B0
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj)
