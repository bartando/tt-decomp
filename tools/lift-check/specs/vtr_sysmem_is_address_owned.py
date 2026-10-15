"""rage::sysMemSimpleAllocator::IsAddressOwned (0x82187558)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::IsAddressOwned"
ADDRESS = 0x82187558
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    base = t.rng.getrandbits(32) & 0x7FFFFFF0
    size = t.rng.choice([0x20, 0x1000, 0x100000])
    t.w32(obj + 0x04, base)
    t.w32(obj + 0x4C, size)
    t.args(r3=obj, r4=(base + t.rng.choice([0, 0x0F, 0x10, 0x11, 0x800, size - 1, size, size + 4])) & 0xFFFFFFFF)
