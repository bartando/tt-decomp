"""Collider guards, four-lane VMX data and observable virtual side effects."""
import struct
from liftcheck.spec import *


def changed(ctx):
    obj = ctx.r(3)
    # Observe all velocity/momentum writes before notification and replace the
    # velocities/limits before the clamp, so reloading after dispatch matters.
    ctx.write(obj + 0x220, ctx.read(obj + 0xe0, 64))
    ctx.write(obj + 0xe0, ctx.read(obj + 0x280, 32))
    ctx.write(obj + 0x90, ctx.read(obj + 0x2a0, 8))
    if struct.unpack('>I', ctx.read(obj + 0x30c, 4))[0]:
        ctx.write(obj + 0x1d0, ctx.read(obj + 0x30c, 4))


def inertia(ctx):
    obj, out = ctx.r(3), ctx.r(4)
    ctx.write(obj + 0x220, ctx.read(obj + 0xf0, 16))
    ctx.write(out, ctx.read(obj + 0x2b0, 64))
    ctx.write(obj + 0xf0, ctx.read(obj + 0x280, 16))
    if struct.unpack('>I', ctx.read(obj + 0x30c, 4))[0]:
        ctx.write(obj + 0x1d0, ctx.read(obj + 0x30c, 4))


CALLS = {
    'motion.vfn_67': model(changed, args=('r3',)),
    'motion.vfn_68': model(changed, args=('r3',)),
    'motion.vfn_13': model(inertia, args=('r3', 'r4', 'r5'), deref={'r3': 0x310}),
    'phCollider_ClampLinearSpeed': run(),
    'phCollider_ClampAngularSpeed': run(),
}


def inputs(t):
    obj = t.alloc(0x330, 'colliderAndGuards') + 16
    t.floats(obj + 0x20, 0x2e0 // 4, -4, 4)
    t.w32(obj, t.vtable('motion', 69))
    t.w32(obj + 0x30c, 0)
    # Squared speed below, at and above the limit, including negative limits.
    limit = t.pick((0., 1., -1., 100., t.f32(-10, 10)))
    t.wf32(obj + 0x90, limit)
    t.wf32(obj + 0x94, -limit)
    for offset in (0xe0, 0xf0):
        if t.index % 4 == 0:
            for i in range(3):
                t.wf32(obj + offset + 4 * i, limit if i == 0 else 0.)
        elif t.index % 4 == 1:
            t.w32(obj + offset + t.rng.randrange(4) * 4, t.pick((1, 0x807fffff, 0x80000000,
                  0x7f800000, 0xff800000, 0x7fc00000)))
    if t.index % 7 == 0:
        t.wf32(obj + 0x68, t.pick((float('inf'), float('nan'), 0., -0., 1e38, 1e-38)))
        t.w32(obj + t.pick((0x100, 0x110, 0x80)), t.pick((1, 0x007fffff, 0x7f800000)))
    vector = t.alloc(48, 'inputAndGuards') + 16
    t.floats(vector, 4, -10, 10)
    if t.index % 3 == 0:
        vector = obj + t.pick((0xe0, 0xf0, 0x100, 0x110, 0x80, 0xa0))
    t.args(r3=obj, r4=vector)
    return obj, vector
