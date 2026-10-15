"""rage::sysMemSimpleAllocator::SetLockState (0x82187880)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::sysMemSimpleAllocator::SetLockState"
ADDRESS = 0x82187880
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"

CALLS = {
    "alloc.vfn_8": stub(ret='void'),
    "alloc.vfn_9": stub(ret='void'),
}


def inputs(t):
    obj = t.alloc(0xC0, "alloc")
    t.w32(obj, t.vtable("alloc", slots=21))
    t.args(r3=obj, r4=t.rng.choice([0, 1]))
