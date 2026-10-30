"""Logging decrements the image counter, with and without an open stream."""
from liftcheck.spec import *

FUNCTION = "rage::sysMemSimpleAllocator::EndLogging"
ADDRESS = 0x82187958
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
CALLS = {0x822E3B38: stub(ret="void", args=("r3",))}


def inputs(t):
    obj = t.alloc(0xC0, "allocator")
    t.w32(obj + 188, t.pick([0, t.alloc(32, "stream")]))
    t.w8(obj + 186, t.pick([0, 1, 255]))
    t.w32(0x825EBD20, t.pick([0, 1, 0xFFFFFFFF, t.u32()]))
    t.args(r3=obj)
