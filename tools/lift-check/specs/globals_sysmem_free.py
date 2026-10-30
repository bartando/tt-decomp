"""Free passes the real shared init lock to SpinAcquire, then releases it."""
from liftcheck.spec import *

FUNCTION = "rage::sysMemSimpleAllocator::Free"
ADDRESS = 0x82187178
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
CALLS = {
    0x82187D90: stub(ret="void", args=("r3",), deref={"r3": 4}),
    "sysMemSimpleAllocator_Free_body": stub(ret="void", args=("r3", "r4")),
}
EXTERNS = {"sysMemSimpleAllocator_Free_body": 0x821871C0}


def inputs(t):
    t.w32(0x825EBCF8, t.u32())
    t.args(r3=t.alloc(0xC0, "allocator"), r4=t.alloc(32, "allocation"))
