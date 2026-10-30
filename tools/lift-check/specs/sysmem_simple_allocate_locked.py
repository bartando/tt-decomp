from liftcheck.spec import *

FUNCTION = "rage::sysMemSimpleAllocator::AllocateLocked"
ADDRESS = 0x82186DA0
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
TRIALS = 1000
def acquire(ctx):
    ctx.write(ctx.r(3), (1).to_bytes(4, "big"))


def allocate(ctx):
    assert int.from_bytes(ctx.read(EXTERNS["g_sysMemAllocatorInitLock"], 4), "big") == 1
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {
    "sysMemSimpleAllocator_SpinAcquire": model(acquire, args=("r3",), deref={"r3": 4}),
    "rage::sysMemSimpleAllocator::Allocate": model(allocate, args=("r3", "r4", "r5")),
}
EXTERNS = {"g_sysMemAllocatorInitLock": 0x825EBCF8, "sysMemSimpleAllocator_SpinAcquire": 0x82187D90, "rage::sysMemSimpleAllocator::Allocate": 0x82186E40}


def inputs(t):
    t.w32(t.sym("g_sysMemAllocatorInitLock"), t.u32())
    t.args(r3=t.alloc(0xC0, "allocator"), r4=t.u32(), r5=t.u32())
