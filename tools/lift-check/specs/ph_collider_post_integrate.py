"""0x822CB360: integrate, publish cached pose, then synchronize current instance."""
import struct
from liftcheck.spec import *
from specs.ph_collider_publish_transform import inputs as setup
FUNCTION = 'rage::phArticulatedCollider::UpdatePostIntegrate'
ADDRESS = 0x822CB360
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FP_CONTRACT = 'off'
FTOL = 1e-99


def integrate(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0xa0, ctx.read(obj + 0x120, 64))
    ctx.write(obj + 0x10, ctx.read(obj + 0x164, 4))


CALLS = {
    'post.vfn_10': model(integrate, args=('r3',)),
    'instance0.vfn_28': stub(ret='void', args=('r3',), deref={'r3': 0x50}),
    'instance1.vfn_28': stub(ret='void', args=('r3',), deref={'r3': 0x50}),
    'phCollider_PublishTransform': run(),
}


def inputs(t):
    setup(t)
    obj = t.reg_args['r3']
    t.w32(obj, t.vtable('post', 11))
    for i, slot in enumerate((0x10, 0x164)):
        instance = t.alloc(0x70, f'instance{i}AndGuards') + 16
        archetype = t.alloc(32, 'archetype')
        bound = t.alloc(0x80, 'bound')
        t.floats(bound + 0x50, 4, -10, 10)
        t.w8(bound + 6, t.pick((0, 1, 0x80)))
        t.w32(archetype + 0xc, bound)
        t.w32(instance, t.vtable(f'instance{i}', 29))
        t.w32(instance + 4, archetype)
        t.w32(obj + slot, instance)
    t.floats(obj + 0x120, 16, -10, 10)
