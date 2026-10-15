"""rage::sysMemSimpleAllocator::Lock (0x82187860)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::Lock"
ADDRESS = 0x82187860
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj)
