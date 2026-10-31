"""Lock order, virtual callback effects and result preservation across unlock."""
import struct
from liftcheck.spec import *
LOCK = 0x825B2324


def enter(ctx):
    ctx.write(ctx.r(3), b'\1')


def leave(ctx):
    assert ctx.read(ctx.r(3), 1) == b'\1'
    ctx.write(ctx.r(3), b'\0')
    ctx.ret(r3=ctx.rng.getrandbits(32))


def add_ref(ctx):
    obj = ctx.r(3)
    assert ctx.read(LOCK, 1) == b'\1'
    owner, replacement, result = struct.unpack('>III', ctx.read(obj + 8, 12))
    ctx.write(obj + 4, ctx.read(LOCK, 1) + bytes(3))
    if owner:
        ctx.write(owner + 0x38, struct.pack('>I', replacement))
    ctx.ret(r3=result)


CALLS = {
    'RtlEnterCriticalSection': model(enter, args=('r3',)),
    'RtlLeaveCriticalSection': model(leave, args=('r3',)),
    'retained.vfn_1': model(add_ref, args=('r3',)),
    'phObject_AddRefLocked': run(),
}


def inputs(t):
    obj = t.alloc(48, 'retainedInterfaceAndGuards') + 16
    t.w32(obj, t.vtable('retained', 2))
    t.w32(obj + 8, 0)
    t.w32(obj + 12, 0)
    t.w32(obj + 16, t.u32())
    t.w8(LOCK, 0)
    t.args(r3=obj)
    return obj
