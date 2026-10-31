"""0x822CABE0: reset identities, preserve W, reload attachments after virtuals."""
import struct
from liftcheck.spec import *
FUNCTION = 'phCollider_Reset'
ADDRESS = 0x822CABE0
SOURCE = 'src/physics/collider_velocity.cpp'
TRIALS = 400
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}


def clear(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x220, ctx.read(obj + 0xa0, 64))
    ctx.write(obj + 0x260, ctx.read(obj + 0x1a0, 16))
    ctx.write(obj + 0x10, ctx.read(obj + 0x300, 4))
    ctx.write(obj + 0x60, ctx.read(obj + 0x304, 4))


def sync(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x20, ctx.read(obj + 0x280, 64))
    ctx.write(obj + 0x60, ctx.read(obj + 0x308, 4))


CALLS = {
    'reset.vfn_2': model(clear, args=('r3',)),
    'reset.vfn_7': model(sync, args=('r3',)),
    'state0.vfn_1': stub(ret='void', args=('r3',), deref={'r3': 0x20}),
    'state1.vfn_1': stub(ret='void', args=('r3',), deref={'r3': 0x20}),
}


def inputs(t):
    obj = t.alloc(0x330, 'colliderAndGuards') + 16
    t.w32(obj, t.vtable('reset', 8))
    bound = t.alloc(16, 'bound')
    t.w32(obj + 0x10, t.pick((0, bound)))
    t.w32(obj + 0x300, t.pick((0, bound)))
    states = []
    for i in range(2):
        state = t.alloc(0x40, 'stateAndGuards') + 16
        t.w32(state, t.vtable(f'state{i}', 2))
        states.append(state)
    for slot in (0x60, 0x304, 0x308):
        t.w32(obj + slot, t.pick((0, *states)))
    t.args(r3=obj)
