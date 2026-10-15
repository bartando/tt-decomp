"""rage::sysMemSimpleAllocator::GetBucketHead (0x82187840)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::GetBucketHead"
ADDRESS = 0x82187840
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj, r4=t.rng.choice([0, 1, 7, 15, 16, 17, 0xFFFFFFFF]))
