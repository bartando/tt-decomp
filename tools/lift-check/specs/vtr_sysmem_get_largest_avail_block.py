"""rage::sysMemSimpleAllocator::GetLargestAvailBlock (0x82187838)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::GetLargestAvailBlock"
ADDRESS = 0x82187838
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj)
