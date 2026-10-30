"""Miniheap uses three image words in start/end/current order."""
from liftcheck.spec import *

FUNCTION = "rage::miniheapAllocator::Allocate"
ADDRESS = 0x823F89B8
SOURCE = "src/rage/misc/rage_misc.cpp"


def inputs(t):
    start = t.alloc(0x1000, "arena")
    end = start + 0x1000
    current = start + t.rng.randrange(0, 0x800)
    t.w32(0x82602808, start)
    t.w32(0x8260280C, end)
    t.w32(0x82602810, current)
    probe = t.pick([start - 1, start, current, end - 1, end, t.u32()])
    t.args(r3=t.alloc(4, "allocator"), r4=t.rng.randrange(0, 128),
           r5=t.pick([4, 8, 16, 32, 64]))
