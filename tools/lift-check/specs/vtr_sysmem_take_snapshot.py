"""rage::sysMemSimpleAllocator::TakeSnapshot (0x821878B8)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::TakeSnapshot"
ADDRESS = 0x821878B8
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.w32(obj + 0xB4, t.rng.randrange(0, 4))
    t.args(r3=obj)
